#!/usr/bin/env python
"""Test full marking workflow with Ollama bypassing CLI"""

import sys
import asyncio
from pathlib import Path
import json

sys.path.insert(0, "src")

from answer_marker.config import settings
from answer_marker.llm.factory import create_llm_client_from_config
from answer_marker.llm.compat import LLMClientCompat
from answer_marker.document_processing import DocumentProcessor
from answer_marker.cli.commands import create_agent_system
from answer_marker.models.marking_guide import MarkingGuide
from answer_marker.models.answer import AnswerSheet, Answer


async def test_full_marking():
    """Test complete marking workflow with Ollama"""

    print("="*70)
    print("TESTING FULL MARKING WORKFLOW WITH OLLAMA")
    print("="*70)

    # Configuration
    marking_guide_path = Path("example/Assessment.pdf")
    answer_sheets_dir = Path("example/")
    output_dir = Path("example/reports")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nConfiguration:")
    print(f"  Provider: {settings.llm_provider}")
    print(f"  Model: {settings.llm_model}")
    print(f"  Marking Guide: {marking_guide_path}")
    print(f"  Answer Sheets: {answer_sheets_dir}")
    print(f"  Output: {output_dir}")

    try:
        # Step 1: Initialize LLM client
        print(f"\n{'='*70}")
        print("STEP 1: Initializing LLM Client")
        print("="*70)

        llm_client = create_llm_client_from_config(settings)
        client = LLMClientCompat(llm_client)
        print("✓ LLM client initialized successfully")

        # Step 2: Initialize document processor and orchestrator
        print(f"\n{'='*70}")
        print("STEP 2: Initializing Document Processor and Agents")
        print("="*70)

        doc_processor = DocumentProcessor(client)
        orchestrator = create_agent_system(client)
        print("✓ Document processor and agents initialized")

        # Step 3: Process marking guide
        print(f"\n{'='*70}")
        print("STEP 3: Processing Marking Guide")
        print("="*70)

        print(f"Processing: {marking_guide_path}")
        marking_guide_data = await doc_processor.process_marking_guide(marking_guide_path)
        marking_guide = MarkingGuide(**marking_guide_data)

        print(f"✓ Marking guide processed successfully")
        print(f"  Questions found: {len(marking_guide.questions)}")
        for i, q in enumerate(marking_guide.questions, 1):
            print(f"    {i}. Question {q.id}: {q.marks} marks")

        # Step 4: Get answer sheet files
        print(f"\n{'='*70}")
        print("STEP 4: Finding Answer Sheets")
        print("="*70)

        answer_sheet_files = [
            f for f in answer_sheets_dir.glob("*.pdf")
            if "Student Answer Sheet" in f.name
        ]

        print(f"✓ Found {len(answer_sheet_files)} answer sheets:")
        for sheet in answer_sheet_files:
            print(f"    • {sheet.name}")

        # Step 5: Mark each answer sheet
        print(f"\n{'='*70}")
        print("STEP 5: Marking Answer Sheets")
        print("="*70)

        reports = []
        for i, sheet_file in enumerate(answer_sheet_files, 1):
            print(f"\n[{i}/{len(answer_sheet_files)}] Processing: {sheet_file.name}")
            print("-" * 70)

            try:
                # Process answer sheet
                expected_questions = [q.id for q in marking_guide.questions]
                print(f"  • Extracting answers...")
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

                print(f"  • Marking with AI agents...")
                print(f"    (This may take a while with local LLM...)")

                # Mark the answer sheet
                report = await orchestrator.mark_answer_sheet(
                    marking_guide=marking_guide,
                    answer_sheet=answer_sheet,
                    assessment_title="Financial Accounting Assessment"
                )

                # Save report
                report_file = output_dir / f"{answer_sheet.student_id}_report.json"
                report.to_json_file(report_file)

                reports.append(report)

                print(f"  ✓ Completed: {answer_sheet.student_id}")
                print(f"    Score: {report.scoring_result.total_marks:.1f}/{report.scoring_result.max_marks:.1f}")
                print(f"    Grade: {report.scoring_result.grade}")
                print(f"    Report saved: {report_file.name}")

            except Exception as e:
                print(f"  ✗ Error marking {sheet_file.name}: {e}")
                import traceback
                traceback.print_exc()
                continue

        # Step 6: Display summary
        print(f"\n{'='*70}")
        print("STEP 6: MARKING SUMMARY")
        print("="*70)

        if reports:
            print(f"\n✓ Successfully marked {len(reports)} answer sheet(s)\n")

            print(f"{'Student ID':<30} {'Score':<15} {'Grade':<10} {'Status':<10}")
            print("-" * 70)

            for report in reports:
                score_str = f"{report.scoring_result.total_marks:.1f}/{report.scoring_result.max_marks:.1f}"
                grade = report.scoring_result.grade
                status = "Pass" if report.scoring_result.passed else "Fail"

                print(f"{report.student_id:<30} {score_str:<15} {grade:<10} {status:<10}")

            # Statistics
            total_students = len(reports)
            passed = sum(1 for r in reports if r.scoring_result.passed)
            failed = total_students - passed
            avg_score = sum(r.scoring_result.percentage for r in reports) / total_students if total_students > 0 else 0
            needs_review = sum(1 for r in reports if r.requires_review)

            print(f"\n{'Statistics:'}")
            print(f"  Total Students: {total_students}")
            print(f"  Passed: {passed}")
            print(f"  Failed: {failed}")
            print(f"  Average Score: {avg_score:.1f}%")
            print(f"  Requires Review: {needs_review}")

            print(f"\n{'Reports saved to:'} {output_dir.absolute()}")
        else:
            print("✗ No answer sheets were successfully marked")

        print(f"\n{'='*70}")
        print("✓ MARKING WORKFLOW COMPLETED SUCCESSFULLY!")
        print("="*70)

        return True

    except Exception as e:
        print(f"\n{'='*70}")
        print(f"✗ ERROR: Marking workflow failed")
        print("="*70)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        result = asyncio.run(test_full_marking())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nMarking interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
