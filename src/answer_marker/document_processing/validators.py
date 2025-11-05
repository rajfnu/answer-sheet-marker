"""Document validators for the Answer Sheet Marker system.

This module validates document quality and completeness before processing.
"""

from typing import Dict, List, Any
from pydantic import BaseModel, Field
from loguru import logger


class ValidationResult(BaseModel):
    """Result of document validation."""

    is_valid: bool = Field(..., description="Whether validation passed")
    errors: List[str] = Field(default_factory=list, description="Critical errors")
    warnings: List[str] = Field(default_factory=list, description="Non-critical warnings")
    quality_score: float = Field(..., ge=0, le=1, description="Quality score (0-1)")


class DocumentValidator:
    """Validate documents before processing.

    Checks document structure, completeness, and quality to catch
    issues early in the processing pipeline.
    """

    def validate_marking_guide(self, structured_data: Dict[str, Any]) -> ValidationResult:
        """Validate marking guide structure.

        Args:
            structured_data: Structured marking guide data

        Returns:
            ValidationResult with errors, warnings, and quality score
        """
        logger.debug("Validating marking guide structure")
        errors = []
        warnings = []

        # Check required fields
        if "questions" not in structured_data:
            errors.append("No questions found in marking guide")
        else:
            questions = structured_data["questions"]

            if not questions:
                errors.append("Marking guide contains no questions")
            else:
                # Check each question
                for i, q in enumerate(questions):
                    self._validate_question(q, i + 1, errors, warnings)

        # Check total marks
        if "total_marks" in structured_data:
            total_marks = structured_data["total_marks"]
            if total_marks <= 0:
                warnings.append("Total marks is 0 or negative")

            # Verify total matches sum of question marks
            if "questions" in structured_data:
                # Convert marks to numbers, handling None and string values
                marks_values = []
                for q in structured_data["questions"]:
                    marks = q.get("marks", 0)
                    if marks is None:
                        marks = 0
                    elif isinstance(marks, str):
                        try:
                            marks = float(marks)
                        except ValueError:
                            marks = 0
                    marks_values.append(marks)

                question_marks_sum = sum(marks_values)
                if abs(question_marks_sum - total_marks) > 0.01:
                    warnings.append(
                        f"Total marks ({total_marks}) doesn't match sum of question marks ({question_marks_sum})"
                    )

        # Calculate quality score
        quality_score = self._calculate_quality_score(structured_data, errors, warnings)

        is_valid = len(errors) == 0

        result = ValidationResult(
            is_valid=is_valid, errors=errors, warnings=warnings, quality_score=quality_score
        )

        if not is_valid:
            logger.error(f"Marking guide validation failed: {errors}")
        elif warnings:
            logger.warning(f"Marking guide has warnings: {warnings}")
        else:
            logger.info(f"Marking guide validation passed (quality: {quality_score:.2f})")

        return result

    def _validate_question(
        self, question: Dict[str, Any], question_num: int, errors: List[str], warnings: List[str]
    ):
        """Validate a single question.

        Args:
            question: Question data
            question_num: Question number (for error messages)
            errors: List to append errors to
            warnings: List to append warnings to
        """
        # Check question ID
        if "id" not in question or not question["id"]:
            errors.append(f"Question {question_num} has no ID")

        # Check question text
        question_text = question.get("question_text", "")
        if not question_text or (isinstance(question_text, str) and not question_text.strip()):
            errors.append(f"Question {question_num} has no text")

        # Check marks
        if "marks" not in question or question["marks"] is None:
            warnings.append(f"Question {question_num} has no marks specified")
        else:
            # Try to convert marks to number
            try:
                marks_value = float(question["marks"]) if isinstance(question["marks"], str) else question["marks"]
                if marks_value <= 0:
                    warnings.append(f"Question {question_num} has 0 or negative marks")
            except (ValueError, TypeError):
                warnings.append(f"Question {question_num} has invalid marks value: {question['marks']}")

        # Check marking scheme
        marking_scheme = question.get("marking_scheme", "")
        if not marking_scheme or (isinstance(marking_scheme, str) and not marking_scheme.strip()):
            warnings.append(f"Question {question_num} has no marking scheme")

        # Check question type
        if "question_type" not in question:
            warnings.append(f"Question {question_num} has no question type specified")

    def validate_answer_sheet(
        self, structured_data: Dict[str, Any], expected_questions: List[str]
    ) -> ValidationResult:
        """Validate answer sheet structure.

        Args:
            structured_data: Structured answer sheet data
            expected_questions: List of expected question IDs

        Returns:
            ValidationResult with errors, warnings, and quality score
        """
        logger.debug(f"Validating answer sheet for {len(expected_questions)} questions")
        errors = []
        warnings = []

        # Check answers field exists
        if "answers" not in structured_data:
            errors.append("No answers found in answer sheet")
        else:
            answers = structured_data["answers"]

            if not answers:
                errors.append("Answer sheet contains no answers")
            else:
                answer_ids = [a["question_id"] for a in answers if "question_id" in a]

                # Check for missing questions
                missing = set(expected_questions) - set(answer_ids)
                if missing:
                    warnings.append(
                        f"Missing answers for questions: {', '.join(sorted(missing))}"
                    )

                # Check for unexpected questions
                unexpected = set(answer_ids) - set(expected_questions)
                if unexpected:
                    warnings.append(
                        f"Unexpected question IDs: {', '.join(sorted(unexpected))}"
                    )

                # Check blank answers
                blank_count = sum(1 for a in answers if a.get("is_blank", False))
                if blank_count > 0:
                    warnings.append(
                        f"{blank_count} unanswered question(s) ({blank_count/len(answers)*100:.1f}%)"
                    )

                # Check answer quality
                for i, answer in enumerate(answers):
                    self._validate_answer(answer, i + 1, errors, warnings)

        # Calculate quality score
        quality_score = self._calculate_quality_score(structured_data, errors, warnings)
        is_valid = len(errors) == 0

        result = ValidationResult(
            is_valid=is_valid, errors=errors, warnings=warnings, quality_score=quality_score
        )

        if not is_valid:
            logger.error(f"Answer sheet validation failed: {errors}")
        elif warnings:
            logger.warning(f"Answer sheet has warnings: {warnings}")
        else:
            logger.info(f"Answer sheet validation passed (quality: {quality_score:.2f})")

        return result

    def _validate_answer(
        self, answer: Dict[str, Any], answer_num: int, errors: List[str], warnings: List[str]
    ):
        """Validate a single answer.

        Args:
            answer: Answer data
            answer_num: Answer number (for error messages)
            errors: List to append errors to
            warnings: List to append warnings to
        """
        # Check question_id
        if "question_id" not in answer or not answer["question_id"]:
            errors.append(f"Answer {answer_num} has no question_id")

        # Check answer_text
        if "answer_text" not in answer:
            errors.append(f"Answer {answer_num} has no answer_text field")
        elif not answer["answer_text"].strip() and not answer.get("is_blank", False):
            warnings.append(
                f"Answer {answer_num} has empty text but is_blank is not set to true"
            )

    def _calculate_quality_score(
        self, data: Dict[str, Any], errors: List[str], warnings: List[str]
    ) -> float:
        """Calculate overall quality score.

        Args:
            data: Document data
            errors: List of errors
            warnings: List of warnings

        Returns:
            Quality score between 0 and 1
        """
        # Start with perfect score
        score = 1.0

        # Deduct for errors (critical)
        score -= len(errors) * 0.2

        # Deduct for warnings (less critical)
        score -= len(warnings) * 0.05

        # Bonus for completeness
        if "questions" in data:
            questions = data["questions"]
            if questions:
                # Check how many questions have marking schemes
                with_schemes = sum(
                    1
                    for q in questions
                    if "marking_scheme" in q
                    and q["marking_scheme"] is not None
                    and isinstance(q["marking_scheme"], str)
                    and q["marking_scheme"].strip()
                )
                scheme_ratio = with_schemes / len(questions)

                # Check how many questions have sample answers
                with_samples = sum(
                    1
                    for q in questions
                    if "sample_answer" in q
                    and q["sample_answer"] is not None
                    and isinstance(q["sample_answer"], str)
                    and q["sample_answer"].strip()
                )
                sample_ratio = with_samples / len(questions)

                # Adjust score based on completeness
                completeness_bonus = (scheme_ratio * 0.1) + (sample_ratio * 0.05)
                score += completeness_bonus

        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))

    def validate_text_extraction(
        self, extracted_text: str, min_length: int = 50
    ) -> ValidationResult:
        """Validate extracted text quality.

        Args:
            extracted_text: Extracted text from document
            min_length: Minimum acceptable text length

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []

        if not extracted_text or len(extracted_text.strip()) < min_length:
            errors.append(
                f"Extracted text is too short ({len(extracted_text.strip())} characters)"
            )

        # Check for garbled text (high ratio of non-alphanumeric characters)
        if extracted_text:
            alphanumeric = sum(c.isalnum() for c in extracted_text)
            total = len(extracted_text)
            ratio = alphanumeric / total if total > 0 else 0

            if ratio < 0.5:
                warnings.append(
                    f"Text may be garbled (only {ratio*100:.1f}% alphanumeric)"
                )

        quality_score = 1.0 - (len(errors) * 0.3) - (len(warnings) * 0.1)
        quality_score = max(0.0, min(1.0, quality_score))

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            quality_score=quality_score,
        )
