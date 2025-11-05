"""CLI commands for the Answer Sheet Marker system."""

import asyncio
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from anthropic import Anthropic
from loguru import logger

from answer_marker.config import settings
from answer_marker.document_processing import DocumentProcessor
from answer_marker.core.orchestrator import create_orchestrator_agent
from answer_marker.agents.question_analyzer import create_question_analyzer_agent
from answer_marker.agents.answer_evaluator import create_answer_evaluator_agent
from answer_marker.agents.scoring_agent import create_scoring_agent
from answer_marker.agents.feedback_generator import create_feedback_generator_agent
from answer_marker.agents.qa_agent import create_qa_agent
from answer_marker.models.marking_guide import MarkingGuide
from answer_marker.models.answer import AnswerSheet, Answer
from answer_marker.models.report import EvaluationReport

app = typer.Typer(
    name="answer-marker",
    help="AI-powered answer sheet marking system using multi-agent architecture",
    add_completion=False,
    rich_markup_mode=None,  # Disable rich help to avoid rendering issues
)
console = Console()


def create_agent_system(client: Anthropic):
    """Create and wire up all agents.

    Args:
        client: Anthropic client instance

    Returns:
        Orchestrator agent with all specialized agents
    """
    # Create specialized agents
    agents = {
        "question_analyzer": create_question_analyzer_agent(client),
        "answer_evaluator": create_answer_evaluator_agent(client),
        "scoring_agent": create_scoring_agent(client),
        "feedback_generator": create_feedback_generator_agent(client),
        "qa_agent": create_qa_agent(client),
    }

    # Create orchestrator
    orchestrator = create_orchestrator_agent(client, agents)

    return orchestrator


@app.command()
def mark(
    marking_guide: str = typer.Option(
        None, "--guide", "-g", help="Path to marking guide PDF"
    ),
    answer_sheets: str = typer.Option(
        None, "--answers", "-a", help="Path to answer sheets directory or single PDF"
    ),
    output_dir: str = typer.Option(
        "./output", "--output", "-o", help="Output directory for reports"
    ),
    assessment_title: str = typer.Option(
        "Assessment", "--title", "-t", help="Assessment title"
    ),
):
    """Mark answer sheets using AI-powered multi-agent system.

    This command processes a marking guide and one or more answer sheets,
    evaluating student responses and generating detailed reports.
    """
    # Validate required arguments
    if not marking_guide or not answer_sheets:
        console.print("[red]Error: Both --guide and --answers are required[/red]")
        raise typer.Exit(code=1)

    # Convert to Path objects
    marking_guide_path = Path(marking_guide)
    answer_sheets_path = Path(answer_sheets)
    output_dir_path = Path(output_dir)

    # Validate paths exist
    if not marking_guide_path.exists():
        console.print(f"[red]Error: Marking guide not found: {marking_guide}[/red]")
        raise typer.Exit(code=1)

    if not answer_sheets_path.exists():
        console.print(f"[red]Error: Answer sheets path not found: {answer_sheets}[/red]")
        raise typer.Exit(code=1)

    console.print(Panel.fit(
        "[bold blue]Answer Sheet Marker[/bold blue]\n"
        "AI-Powered Multi-Agent Marking System",
        border_style="blue"
    ))

    # Display configuration
    console.print(f"\n[cyan]Marking Guide:[/cyan] {marking_guide_path}")
    console.print(f"[cyan]Answer Sheets:[/cyan] {answer_sheets_path}")
    console.print(f"[cyan]Output Directory:[/cyan] {output_dir_path}")
    console.print(f"[cyan]Assessment Title:[/cyan] {assessment_title}\n")

    # Create output directory
    output_dir_path.mkdir(parents=True, exist_ok=True)

    # Run async marking process
    asyncio.run(_mark_async(marking_guide_path, answer_sheets_path, output_dir_path, assessment_title))


async def _mark_async(
    marking_guide_path: Path,
    answer_sheets_path: Path,
    output_dir: Path,
    assessment_title: str,
):
    """Async implementation of marking workflow."""

    try:
        # Initialize client and processors
        client = Anthropic(api_key=settings.anthropic_api_key)
        doc_processor = DocumentProcessor(client)
        orchestrator = create_agent_system(client)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:

            # Step 1: Process marking guide
            task1 = progress.add_task(
                "[cyan]Processing marking guide...", total=None
            )

            marking_guide_data = await doc_processor.process_marking_guide(marking_guide_path)

            # Convert to MarkingGuide model
            marking_guide = MarkingGuide(**marking_guide_data)

            progress.update(
                task1,
                description=f"[green]✓ Marking guide processed ({len(marking_guide.questions)} questions)",
                completed=True
            )

            # Step 2: Get answer sheet files
            if answer_sheets_path.is_file():
                answer_sheet_files = [answer_sheets_path]
            else:
                answer_sheet_files = list(answer_sheets_path.glob("*.pdf"))

            if not answer_sheet_files:
                console.print("[red]✗ No PDF files found in the answer sheets directory[/red]")
                return

            console.print(f"\n[cyan]Found {len(answer_sheet_files)} answer sheet(s) to mark[/cyan]\n")

            # Step 3: Mark each answer sheet
            task2 = progress.add_task(
                "[cyan]Marking answer sheets...",
                total=len(answer_sheet_files)
            )

            reports = []
            for i, sheet_file in enumerate(answer_sheet_files, 1):
                progress.update(
                    task2,
                    description=f"[cyan]Marking {sheet_file.name} ({i}/{len(answer_sheet_files)})..."
                )

                try:
                    # Process answer sheet
                    expected_questions = [q.id for q in marking_guide.questions]
                    answer_sheet_data = await doc_processor.process_answer_sheet(
                        sheet_file, expected_questions
                    )

                    # Convert to AnswerSheet model
                    answers = [
                        Answer(
                            question_id=ans["question_id"],
                            answer_text=ans.get("answer_text", ""),
                            is_blank=ans.get("is_blank", False)
                        )
                        for ans in answer_sheet_data.get("answers", [])
                    ]

                    answer_sheet = AnswerSheet(
                        student_id=answer_sheet_data.get("student_id", sheet_file.stem),
                        answers=answers
                    )

                    # Mark the answer sheet
                    report = await orchestrator.mark_answer_sheet(
                        marking_guide=marking_guide,
                        answer_sheet=answer_sheet,
                        assessment_title=assessment_title
                    )

                    # Save report
                    report_file = output_dir / f"{answer_sheet.student_id}_report.json"
                    report.to_json_file(report_file)

                    reports.append(report)

                    progress.update(task2, advance=1)

                except Exception as e:
                    logger.error(f"Error marking {sheet_file.name}: {e}")
                    console.print(f"[red]✗ Error marking {sheet_file.name}: {e}[/red]")
                    progress.update(task2, advance=1)

            progress.update(
                task2,
                description=f"[green]✓ Marked {len(reports)} answer sheet(s)",
            )

        # Display summary
        console.print("\n" + "="*70 + "\n")
        console.print("[bold green]✓ Marking Completed![/bold green]\n")

        if reports:
            _display_summary(reports, output_dir)

    except Exception as e:
        logger.error(f"Marking process failed: {e}")
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}")
        raise typer.Exit(code=1)


def _display_summary(reports: list[EvaluationReport], output_dir: Path):
    """Display summary table of marking results."""

    table = Table(title="Marking Summary", show_header=True, header_style="bold cyan")
    table.add_column("Student ID", style="cyan")
    table.add_column("Score", justify="right")
    table.add_column("Grade", justify="center", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Review", justify="center")

    for report in reports:
        score_str = f"{report.scoring_result.total_marks:.1f}/{report.scoring_result.max_marks:.1f}"

        # Color grade based on performance
        grade = report.scoring_result.grade
        if grade.startswith("A"):
            grade_colored = f"[green]{grade}[/green]"
        elif grade.startswith("B"):
            grade_colored = f"[blue]{grade}[/blue]"
        elif grade.startswith("C"):
            grade_colored = f"[yellow]{grade}[/yellow]"
        else:
            grade_colored = f"[red]{grade}[/red]"

        status = "[green]✓ Pass[/green]" if report.scoring_result.passed else "[red]✗ Fail[/red]"

        review = ""
        if report.requires_review:
            if report.review_priority == "high":
                review = "[red]⚠ High[/red]"
            elif report.review_priority == "medium":
                review = "[yellow]⚠ Medium[/yellow]"
            else:
                review = "[blue]⚠ Low[/blue]"
        else:
            review = "[green]—[/green]"

        table.add_row(
            report.student_id,
            score_str,
            grade_colored,
            status,
            review
        )

    console.print(table)
    console.print(f"\n[cyan]Reports saved to:[/cyan] {output_dir}")

    # Calculate statistics
    total_students = len(reports)
    passed = sum(1 for r in reports if r.scoring_result.passed)
    failed = total_students - passed
    avg_score = sum(r.scoring_result.percentage for r in reports) / total_students if total_students > 0 else 0
    needs_review = sum(1 for r in reports if r.requires_review)

    console.print(f"\n[bold]Statistics:[/bold]")
    console.print(f"  Total Students: {total_students}")
    console.print(f"  Passed: [green]{passed}[/green]")
    console.print(f"  Failed: [red]{failed}[/red]")
    console.print(f"  Average Score: {avg_score:.1f}%")
    console.print(f"  Requires Review: [yellow]{needs_review}[/yellow]")


@app.command()
def calibrate(
    marking_guide: str = typer.Option(
        None, "--guide", "-g", help="Path to marking guide PDF"
    ),
    sample_answer: str = typer.Option(
        None, "--sample", "-s", help="Path to sample answer PDF"
    ),
    expected_score: float = typer.Option(
        None, "--score", "-sc", help="Expected score for the sample answer"
    ),
):
    """Calibrate the marking system with a sample answer.

    Use this command to test the marking system against a known answer
    and compare the AI's assessment with the expected score.
    """
    # Validate required arguments
    if not marking_guide or not sample_answer or expected_score is None:
        console.print("[red]Error: --guide, --sample, and --score are required[/red]")
        raise typer.Exit(code=1)

    # Convert to Path objects
    marking_guide_path = Path(marking_guide)
    sample_answer_path = Path(sample_answer)

    # Validate paths exist
    if not marking_guide_path.exists():
        console.print(f"[red]Error: Marking guide not found: {marking_guide}[/red]")
        raise typer.Exit(code=1)

    if not sample_answer_path.exists():
        console.print(f"[red]Error: Sample answer not found: {sample_answer}[/red]")
        raise typer.Exit(code=1)

    console.print(Panel.fit(
        "[bold blue]Calibration Mode[/bold blue]\n"
        "Test marking accuracy with sample answers",
        border_style="blue"
    ))

    console.print(f"\n[cyan]Marking Guide:[/cyan] {marking_guide_path}")
    console.print(f"[cyan]Sample Answer:[/cyan] {sample_answer_path}")
    console.print(f"[cyan]Expected Score:[/cyan] {expected_score}\n")

    asyncio.run(_calibrate_async(marking_guide_path, sample_answer_path, expected_score))


async def _calibrate_async(
    marking_guide_path: Path,
    sample_answer_path: Path,
    expected_score: float
):
    """Async implementation of calibration."""

    try:
        # Initialize system
        client = Anthropic(api_key=settings.anthropic_api_key)
        doc_processor = DocumentProcessor(client)
        orchestrator = create_agent_system(client)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            # Process marking guide
            task1 = progress.add_task("[cyan]Processing marking guide...", total=None)
            marking_guide_data = await doc_processor.process_marking_guide(marking_guide_path)
            marking_guide = MarkingGuide(**marking_guide_data)
            progress.update(task1, description="[green]✓ Marking guide processed", completed=True)

            # Process sample answer
            task2 = progress.add_task("[cyan]Processing sample answer...", total=None)
            expected_questions = [q.id for q in marking_guide.questions]
            answer_data = await doc_processor.process_answer_sheet(
                sample_answer_path, expected_questions
            )

            answers = [
                Answer(
                    question_id=ans["question_id"],
                    answer_text=ans.get("answer_text", ""),
                    is_blank=ans.get("is_blank", False)
                )
                for ans in answer_data.get("answers", [])
            ]

            answer_sheet = AnswerSheet(
                student_id="calibration_sample",
                answers=answers
            )

            progress.update(task2, description="[green]✓ Sample answer processed", completed=True)

            # Mark the sample
            task3 = progress.add_task("[cyan]Marking sample answer...", total=None)
            report = await orchestrator.mark_answer_sheet(
                marking_guide=marking_guide,
                answer_sheet=answer_sheet,
                assessment_title="Calibration"
            )
            progress.update(task3, description="[green]✓ Marking completed", completed=True)

        # Display calibration results
        console.print("\n" + "="*70 + "\n")
        console.print("[bold]Calibration Results:[/bold]\n")

        actual_score = report.scoring_result.total_marks
        max_score = report.scoring_result.max_marks
        difference = actual_score - expected_score
        percent_diff = (difference / max_score * 100) if max_score > 0 else 0

        table = Table(show_header=False, box=None)
        table.add_column(style="cyan")
        table.add_column(style="white")

        table.add_row("Expected Score:", f"{expected_score:.1f} / {max_score:.1f}")
        table.add_row("AI Score:", f"{actual_score:.1f} / {max_score:.1f}")
        table.add_row("Grade:", report.scoring_result.grade)
        table.add_row("Difference:", f"{difference:+.1f} ({percent_diff:+.1f}%)")

        console.print(table)

        # Interpretation
        console.print()
        if abs(percent_diff) < 5:
            console.print("[green]✓ Excellent calibration! The AI score is very close to expected.[/green]")
        elif abs(percent_diff) < 10:
            console.print("[yellow]⚠ Good calibration. Consider reviewing the marking criteria.[/yellow]")
        else:
            console.print("[red]⚠ Significant difference detected. Review marking guide and criteria.[/red]")

        console.print(f"\n[cyan]Confidence Level:[/cyan] {report.qa_result.confidence_level}")
        console.print(f"[cyan]Consistency Score:[/cyan] {report.qa_result.consistency_score:.2f}")

        if report.qa_result.flags:
            console.print(f"\n[yellow]QA Flags ({len(report.qa_result.flags)}):[/yellow]")
            for flag in report.qa_result.flags:
                console.print(f"  • {flag.reason} (severity: {flag.severity})")

    except Exception as e:
        logger.error(f"Calibration failed: {e}")
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def report(
    report_file: str = typer.Argument(
        help="Path to report JSON file"
    ),
):
    """Display a detailed report from a previously completed marking session.

    This command reads a saved report JSON file and displays it in a
    formatted, human-readable way.
    """
    try:
        # Convert to Path and validate
        report_file_path = Path(report_file)

        if not report_file_path.exists():
            console.print(f"[red]Error: Report file not found: {report_file}[/red]")
            raise typer.Exit(code=1)

        # Load report
        report = EvaluationReport.from_json_file(report_file_path)

        # Display header
        console.print(Panel.fit(
            f"[bold blue]Evaluation Report[/bold blue]\n"
            f"Student: {report.student_id}\n"
            f"Assessment: {report.assessment_title}",
            border_style="blue"
        ))

        # Overall scores
        console.print("\n[bold]Overall Results:[/bold]")
        table = Table(show_header=False, box=None)
        table.add_column(style="cyan")
        table.add_column(style="white")

        table.add_row("Score:", f"{report.scoring_result.total_marks:.1f} / {report.scoring_result.max_marks:.1f}")
        table.add_row("Percentage:", f"{report.scoring_result.percentage:.1f}%")
        table.add_row("Grade:", report.scoring_result.grade)
        table.add_row("Status:", "[green]Pass[/green]" if report.scoring_result.passed else "[red]Fail[/red]")
        table.add_row("Processing Time:", f"{report.processing_time:.2f}s")

        console.print(table)

        # Question-by-question breakdown
        console.print("\n[bold]Question Breakdown:[/bold]")
        for i, eval in enumerate(report.question_evaluations, 1):
            console.print(f"\n[cyan]Question {i} (ID: {eval.question_id}):[/cyan]")
            console.print(f"  Score: {eval.marks_awarded:.1f} / {eval.max_marks:.1f}")
            console.print(f"  Quality: {eval.overall_quality}")
            console.print(f"  Confidence: {eval.confidence_score:.2f}")

            if eval.strengths:
                console.print("  [green]Strengths:[/green]")
                for strength in eval.strengths:
                    console.print(f"    • {strength}")

            if eval.weaknesses:
                console.print("  [yellow]Weaknesses:[/yellow]")
                for weakness in eval.weaknesses:
                    console.print(f"    • {weakness}")

        # Feedback
        console.print("\n[bold]Feedback:[/bold]")
        console.print(f"\n{report.feedback_report.overall_feedback}")

        if report.feedback_report.key_strengths:
            console.print("\n[green]Key Strengths:[/green]")
            for strength in report.feedback_report.key_strengths:
                console.print(f"  • {strength}")

        if report.feedback_report.key_improvements:
            console.print("\n[yellow]Areas for Improvement:[/yellow]")
            for improvement in report.feedback_report.key_improvements:
                console.print(f"  • {improvement}")

        # QA information
        console.print("\n[bold]Quality Assurance:[/bold]")
        console.print(f"  QA Status: {'[green]Passed[/green]' if report.qa_result.passed else '[red]Failed[/red]'}")
        console.print(f"  Confidence Level: {report.qa_result.confidence_level}")
        console.print(f"  Requires Review: {'[yellow]Yes[/yellow]' if report.requires_review else '[green]No[/green]'}")

        if report.requires_review:
            console.print(f"  Review Priority: {report.review_priority}")

        if report.qa_result.flags:
            console.print(f"\n  [yellow]QA Flags:[/yellow]")
            for flag in report.qa_result.flags:
                console.print(f"    • {flag.reason} (severity: {flag.severity})")

    except Exception as e:
        logger.error(f"Failed to load report: {e}")
        console.print(f"[red]✗ Error loading report: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def version():
    """Display version information."""
    console.print("[bold blue]Answer Sheet Marker[/bold blue]")
    console.print("Version: 0.1.0")
    console.print("AI Model: Claude Sonnet 4.5")
    console.print("\nMulti-Agent Architecture:")
    console.print("  • Question Analyzer")
    console.print("  • Answer Evaluator")
    console.print("  • Scoring Agent")
    console.print("  • Feedback Generator")
    console.print("  • QA Agent")
    console.print("  • Orchestrator")


if __name__ == "__main__":
    app()
