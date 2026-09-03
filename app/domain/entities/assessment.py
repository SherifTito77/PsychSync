# app/domain/entities/assessment.py
"""
Assessment Domain Entity

Pure business object representing an Assessment.
Independent of database models and API frameworks.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from app.domain.exceptions import BusinessRuleError, ValidationError


class AssessmentStatus(Enum):
    """Assessment lifecycle status"""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class AssessmentCategory(Enum):
    """Assessment categories"""

    PERSONALITY = "personality"
    COGNITIVE = "cognitive"
    CLINICAL = "clinical"
    BEHAVIORAL = "behavioral"
    DEVELOPMENTAL = "developmental"
    NEUROPSYCHOLOGICAL = "neuropsychological"
    EDUCATIONAL = "educational"
    CAREER = "career"
    OTHER = "other"


@dataclass
class AssessmentSection:
    """
    Assessment section domain entity.

    Represents a logical grouping of questions within an assessment.
    """

    id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: Optional[str] = None
    order: int = 0
    time_limit: Optional[int] = None  # in seconds
    question_count: int = 0


@dataclass
class AssessmentQuestion:
    """
    Assessment question domain entity.
    """

    id: UUID = field(default_factory=uuid4)
    section_id: UUID = field(default_factory=uuid4)
    question_type: str = "text"  # multiple_choice, rating_scale, text, etc.
    question_text: str = ""
    help_text: Optional[str] = None
    order: int = 0
    is_required: bool = True
    config: dict = field(default_factory=dict)


@dataclass
class Assessment:
    """
    Assessment domain entity.

    This is a pure business object that encapsulates assessment-related
    business logic. It's independent of database concerns.

    Attributes:
        id: Unique identifier
        title: Assessment title
        description: Detailed description
        category: Assessment category
        status: Current status (draft, published, archived)
        instructions: Instructions for respondents
        estimated_duration: Estimated time to complete (minutes)
        is_public: Whether assessment is publicly accessible
        allow_anonymous: Whether anonymous responses are allowed
        randomize_questions: Whether to randomize question order
        show_progress: Whether to show progress to respondents
        created_by: User who created assessment
        team_id: Team ID (if team-specific)
        version: Assessment version
        sections: List of sections
        question_count: Total number of questions
        published_at: Publication timestamp
        created_at: Creation timestamp
        updated_at: Last update timestamp

    Example:
        >>> assessment = Assessment.create(
        ...     title="MBTI Assessment",
        ...     category=AssessmentCategory.PERSONALITY,
        ...     created_by=user
        ... )
        >>> assessment.publish()
        >>> assessment.status
        <AssessmentStatus.PUBLISHED: 'published'>
    """

    # Assessment details
    title: str
    description: Optional[str] = None
    category: AssessmentCategory = AssessmentCategory.OTHER
    status: AssessmentStatus = AssessmentStatus.DRAFT
    instructions: Optional[str] = None

    # Primary identifier
    id: UUID = field(default_factory=uuid4)
    estimated_duration: Optional[int] = None  # in minutes

    # Settings
    is_public: bool = False
    allow_anonymous: bool = False
    randomize_questions: bool = False
    show_progress: bool = True

    # Ownership
    created_by_id: UUID = field(default_factory=uuid4)
    team_id: Optional[UUID] = None

    # Versioning
    version: int = 1

    # Content
    sections: list[AssessmentSection] = field(default_factory=list)
    question_count: int = 0

    # Timestamps
    published_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # ========================================================================
    # FACTORY METHODS
    # ========================================================================

    @classmethod
    def create(
        cls,
        title: str,
        category: AssessmentCategory,
        created_by_id: UUID,
        description: Optional[str] = None,
        team_id: Optional[UUID] = None,
    ) -> "Assessment":
        """
        Create a new assessment.

        Args:
            title: Assessment title (3-200 characters)
            category: Assessment category
            created_by_id: ID of user creating assessment
            description: Optional description
            team_id: Optional team ID for team-specific assessments

        Returns:
            New Assessment instance

        Raises:
            ValidationError: If validation fails

        Example:
            >>> assessment = Assessment.create(
            ...     title="MBTI Assessment",
            ...     category=AssessmentCategory.PERSONALITY,
            ...     created_by_id=user_id
            ... )
        """
        # Validate title
        if len(title.strip()) < 3:
            raise ValidationError("Title must be at least 3 characters")
        if len(title) > 200:
            raise ValidationError("Title must not exceed 200 characters")

        return cls(
            title=title.strip(),
            description=description,
            category=category,
            created_by_id=created_by_id,
            team_id=team_id,
            status=AssessmentStatus.DRAFT,
            version=1,
        )

    # ========================================================================
    # BUSINESS LOGIC METHODS
    # ========================================================================

    def publish(self) -> None:
        """
        Publish the assessment.

        Raises:
            BusinessRuleError: If assessment has no questions
            BusinessRuleError: If already published

        Example:
            >>> assessment.publish()
            >>> assessment.is_published()
            True
        """
        if self.status == AssessmentStatus.PUBLISHED:
            raise BusinessRuleError("Assessment is already published")

        if self.question_count == 0:
            raise BusinessRuleError("Cannot publish assessment with no questions")

        self.status = AssessmentStatus.PUBLISHED
        self.published_at = datetime.utcnow()
        self._touch()

    def archive(self) -> None:
        """
        Archive the assessment.

        Example:
            >>> assessment.archive()
            >>> assessment.status
            <AssessmentStatus.ARCHIVED: 'archived'>
        """
        self.status = AssessmentStatus.ARCHIVED
        self._touch()

    def add_section(self, section: AssessmentSection) -> None:
        """
        Add a section to the assessment.

        Args:
            section: Section to add

        Example:
            >>> section = AssessmentSection(title="Personality Questions")
            >>> assessment.add_section(section)
        """
        self.sections.append(section)
        self._recalculate_question_count()
        self._touch()

    def remove_section(self, section_id: UUID) -> None:
        """
        Remove a section from the assessment.

        Args:
            section_id: ID of section to remove

        Example:
            >>> assessment.remove_section(section_id)
        """
        self.sections = [s for s in self.sections if s.id != section_id]
        self._recalculate_question_count()
        self._touch()

    def update_content(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        instructions: Optional[str] = None,
    ) -> None:
        """
        Update assessment content.

        Args:
            title: New title
            description: New description
            instructions: New instructions

        Raises:
            ValidationError: If title is invalid

        Example:
            >>> assessment.update_content(title="New Title")
        """
        if title is not None:
            if len(title.strip()) < 3:
                raise ValidationError("Title must be at least 3 characters")
            if len(title) > 200:
                raise ValidationError("Title must not exceed 200 characters")
            self.title = title.strip()

        if description is not None:
            self.description = description

        if instructions is not None:
            self.instructions = instructions

        self._touch()

    def can_be_taken_by_user(self, user_id: UUID) -> bool:
        """
        Check if user can take this assessment.

        Args:
            user_id: ID of user

        Returns:
            True if user can take assessment

        Example:
            >>> if assessment.can_be_taken_by_user(user_id):
            ...     print("User can take assessment")
        """
        # Must be published
        if self.status != AssessmentStatus.PUBLISHED:
            return False

        # Must be public or owned by user's team
        if not self.is_public:
            # Team-specific assessments require team membership
            if self.team_id is None:
                return False

        return True

    def is_published(self) -> bool:
        """Check if assessment is published"""
        return self.status == AssessmentStatus.PUBLISHED

    def is_draft(self) -> bool:
        """Check if assessment is in draft status"""
        return self.status == AssessmentStatus.DRAFT

    def is_archived(self) -> bool:
        """Check if assessment is archived"""
        return self.status == AssessmentStatus.ARCHIVED

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _recalculate_question_count(self) -> None:
        """Recalculate total question count from sections"""
        self.question_count = sum(s.question_count for s in self.sections)

    def _touch(self) -> None:
        """Update the updated_at timestamp"""
        self.updated_at = datetime.utcnow()

    # ========================================================================
    # SERIALIZATION
    # ========================================================================

    def to_dict(self) -> dict:
        """
        Convert assessment to dictionary.

        Returns:
            Dictionary representation

        Example:
            >>> data = assessment.to_dict()
            >>> print(data['title'])
            'MBTI Assessment'
        """
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "status": self.status.value,
            "instructions": self.instructions,
            "estimated_duration": self.estimated_duration,
            "is_public": self.is_public,
            "allow_anonymous": self.allow_anonymous,
            "randomize_questions": self.randomize_questions,
            "show_progress": self.show_progress,
            "created_by_id": str(self.created_by_id),
            "team_id": str(self.team_id) if self.team_id else None,
            "version": self.version,
            "question_count": self.question_count,
            "published_at": (
                self.published_at.isoformat() if self.published_at else None
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "sections": [self._section_to_dict(s) for s in self.sections],
        }

    def _section_to_dict(self, section: AssessmentSection) -> dict:
        """Convert section to dictionary"""
        return {
            "id": str(section.id),
            "title": section.title,
            "description": section.description,
            "order": section.order,
            "time_limit": section.time_limit,
            "question_count": section.question_count,
        }

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"Assessment(id={self.id}, title={self.title}, status={self.status.value})"
        )
