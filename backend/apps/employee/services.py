from django.db import transaction

from apps.employee.models import (
Employee,
EmployeeAssignment,
EmployeeContact,
EmployeeIdentity,
Employment,
NextOfKin,
EmergencyContact,
EmployeeDocument,
)

from django.utils import timezone
from django.db import transaction

class EmployeeService:

    @staticmethod
    def get_user_organization(user):
        if not user.is_authenticated:
            return None

        employee = Employee.objects.filter(
            user=user,
            is_active=True,
        ).select_related(
            "organization"
        ).first()

        if not employee:
            return None

        return employee.organization


    @staticmethod
    @transaction.atomic
    def create_employee(
        *,
        organization,
        first_name,
        last_name,
        employee_number=None,
        middle_name="",
        date_of_birth=None,
        gender="",
        personal_email="",
        company_email="",
        phone_number="",
        address="",
        branch=None,
        department=None,
        team=None,
        position=None,
        job_grade=None,
        manager=None,
        employment_type=Employment.EmploymentType.PERMANENT,
        employment_status=Employment.EmploymentStatus.PROBATION,
        offer_date=None,
        employment_start_date=None,
        probation_end_date=None,
        confirmation_status=Employment.ConfirmationStatus.PENDING,
        confirmation_date=None,
        date_left=None,
        user=None,
    ):
        EmployeeService._validate_organization_assignment(
            organization=organization,
            branch=branch,
            department=department,
            team=team,
            position=position,
            job_grade=job_grade,
            manager=manager,
        )

        if not employee_number:
            employee_number = EmployeeService.generate_employee_number(
                organization
            )

        employee = Employee.objects.create(
            organization=organization,
            employee_number=employee_number,
            user=user,
        )

        EmployeeIdentity.objects.create(
            employee=employee,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            gender=gender,
        )

        EmployeeContact.objects.create(
            employee=employee,
            personal_email=personal_email,
            company_email=company_email,
            phone_number=phone_number,
            address=address,
        )

        EmployeeAssignment.objects.create(
            employee=employee,
            branch=branch,
            department=department,
            team=team,
            position=position,
            job_grade=job_grade,
            manager=manager,
        )

        Employment.objects.create(
            employee=employee,
            employment_type=employment_type,
            employment_status=employment_status,
            offer_date=offer_date,
            employment_start_date=employment_start_date,
            probation_end_date=probation_end_date,
            confirmation_status=confirmation_status,
            confirmation_date=confirmation_date,
            date_left=date_left,
        )

        return employee

    @staticmethod
    def _validate_organization_assignment(
        *,
        organization,
        branch=None,
        department=None,
        team=None,
        position=None,
        job_grade=None,
        manager=None,
    ):
        # -----------------------------------------
        # Branch
        # -----------------------------------------

        if branch is not None:
            if branch.organization_id != organization.id:
                raise ValueError(
                    "Branch does not belong to the employee's organization."
                )

        # -----------------------------------------
        # Department
        # -----------------------------------------

        if department is not None:
            if department.organization_id != organization.id:
                raise ValueError(
                    "Department does not belong to the employee's organization."
                )

        # -----------------------------------------
        # Team
        # -----------------------------------------

        if team is not None:
            if team.department.organization_id != organization.id:
                raise ValueError(
                    "Team does not belong to the employee's organization."
                )

        # -----------------------------------------
        # Position
        # -----------------------------------------

        if position is not None:
            if position.organization_id != organization.id:
                raise ValueError(
                    "Position does not belong to the employee's organization."
                )

        # -----------------------------------------
        # Job Grade
        # -----------------------------------------

        if job_grade is not None:
            if job_grade.organization_id != organization.id:
                raise ValueError(
                    "Job grade does not belong to the employee's organization."
                )

        # -----------------------------------------
        # Manager
        # -----------------------------------------

        if manager is not None:
            if manager.organization_id != organization.id:
                raise ValueError(
                    "Manager does not belong to the employee's organization."
                )

    @staticmethod
    def generate_employee_number(organization):
        last_employee = (
            Employee.objects
            .filter(organization=organization)
            .order_by("-created_at")
            .first()
        )

        if not last_employee:
            return "EMP-000001"

        try:
            last_number = int(
                last_employee.employee_number.split("-")[-1]
            )
        except (ValueError, AttributeError):
            last_number = 0

        return f"EMP-{last_number + 1:06d}"


    @staticmethod
    @transaction.atomic
    def add_next_of_kin(
        *,
        employee,
        full_name,
        relationship,
        phone_number,
        email="",
        address="",
        is_primary=False,
    ):
        if is_primary:
            NextOfKin.objects.filter(
                employee=employee,
                is_primary=True,
            ).update(is_primary=False)

        return NextOfKin.objects.create(
            employee=employee,
            full_name=full_name,
            relationship=relationship,
            phone_number=phone_number,
            email=email,
            address=address,
            is_primary=is_primary,
        )


    @staticmethod
    @transaction.atomic
    def add_emergency_contact(
        *,
        employee,
        full_name,
        relationship="",
        phone_number="",
        alternative_phone_number="",
        email="",
        address="",
        is_primary=False,
    ):
        if is_primary:
            EmergencyContact.objects.filter(
                employee=employee,
                is_primary=True,
            ).update(is_primary=False)

        return EmergencyContact.objects.create(
            employee=employee,
            full_name=full_name,
            relationship=relationship,
            phone_number=phone_number,
            alternative_phone_number=alternative_phone_number,
            email=email,
            address=address,
            is_primary=is_primary,
        )

    @staticmethod
    def get_employee_queryset():
        return (
            Employee.objects
            .select_related(
                "organization",
                "user",
                "identity",
                "contact",
                "assignment",
                "assignment__branch",
                "assignment__department",
                "assignment__team",
                "assignment__position",
                "assignment__job_grade",
                "assignment__manager",
                "employment",
            )
            .prefetch_related(
                "next_of_kin",
                "emergency_contacts",
                "documents",
            )
        )

    @staticmethod
    def list_employees(*, organization=None):
        queryset = EmployeeService.get_employee_queryset()

        if organization is not None:
            queryset = queryset.filter(
                organization=organization
            )

        return queryset

    @staticmethod
    def get_employee(
        *,
        employee_id,
        organization=None,
    ):
        queryset = EmployeeService.get_employee_queryset()

        filters = {
            "id": employee_id,
        }

        if organization is not None:
            filters["organization"] = organization

        return queryset.get(**filters)

    def patch(
        self,
        request,
        organization_id,
        employee_id,
    ):

        # -----------------------------------
        # Validate employee
        # -----------------------------------

        try:

            employee = EmployeeService.get_employee(
                employee_id=employee_id,
                organization=request.organization,
            )

        except Employee.DoesNotExist:

            return Response(
                {
                    "detail": "Employee not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # -----------------------------------
        # Validate request data
        # -----------------------------------

        serializer = EmployeeUpdateSerializer(
            employee,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        # -----------------------------------
        # Update employee
        # -----------------------------------

        serializer.save()

        # -----------------------------------
        # Return updated employee
        # -----------------------------------

        response_serializer = EmployeeSerializer(
            employee
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )


    @staticmethod
    @transaction.atomic
    def update_employee(
        *,
        employee,
        identity_data=None,
        contact_data=None,
        assignment_data=None,
        employment_data=None,
    ):
        """
        Update an employee and their related records.

        All assignment objects must belong to the
        employee's organization.
        """

        assignment_data = assignment_data or {}

        # -----------------------------------------
        # Employee organization
        # -----------------------------------------

        organization = employee.organization

        # -----------------------------------------
        # Identity
        # -----------------------------------------

        if identity_data:

            identity = employee.identity

            for field, value in identity_data.items():
                setattr(
                    identity,
                    field,
                    value,
                )

            identity.save()

        # -----------------------------------------
        # Contact
        # -----------------------------------------

        if contact_data:

            contact = employee.contact

            for field, value in contact_data.items():
                setattr(
                    contact,
                    field,
                    value,
                )

            contact.save()

        # -----------------------------------------
        # Assignment
        # -----------------------------------------

        if assignment_data:

            branch = assignment_data.get(
                "branch"
            )

            department = assignment_data.get(
                "department"
            )

            team = assignment_data.get(
                "team"
            )

            position = assignment_data.get(
                "position"
            )

            job_grade = assignment_data.get(
                "job_grade"
            )

            manager = assignment_data.get(
                "manager"
            )

            # -----------------------------------------
            # Validate organization ownership
            # -----------------------------------------

            EmployeeService._validate_organization_assignment(
                organization=organization,
                branch=branch,
                department=department,
                team=team,
                position=position,
                job_grade=job_grade,
                manager=manager,
            )

            assignment = employee.assignment

            for field, value in assignment_data.items():

                setattr(
                    assignment,
                    field,
                    value,
                )

            assignment.save()

        # -----------------------------------------
        # Employment
        # -----------------------------------------

        if employment_data:

            employment = employee.employment

            for field, value in employment_data.items():

                setattr(
                    employment,
                    field,
                    value,
                )

            employment.save()

        return employee

    @staticmethod
    @transaction.atomic
    def deactivate_employee(
        *,
        employee,
    ):
        """
        Deactivate an employee.
    
        The employee record is preserved and only
        marked as inactive.
        """
    
        employee.is_active = False
        employee.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )
    
        return employee

    @staticmethod
    def get_employee_for_organization(
        *,
        employee_id,
        organization,
    ):
        return (
            EmployeeService
            .get_employee_queryset()
            .get(
                id=employee_id,
                organization=organization,
            )
        )

class EmployeeDocumentService:

    @staticmethod
    def list_documents(
        *,
        employee,
    ):
        return (
            EmployeeDocument.objects
            .filter(
                employee=employee,
            )
            .order_by(
                "-created_at"
            )
        )

    @staticmethod
    def get_document(
        *,
        employee,
        document_id,
    ):
        return (
            EmployeeDocument.objects
            .get(
                id=document_id,
                employee=employee,
                is_archived=False,
            )
        )

    @staticmethod
    @transaction.atomic
    def create_document(
        *,
        employee,
        document_type,
        name,
        file,
        description="",
        issue_date=None,
        expiry_date=None,
    ):
        return EmployeeDocument.objects.create(
            employee=employee,
            document_type=document_type,
            name=name,
            file=file,
            description=description,
            issue_date=issue_date,
            expiry_date=expiry_date,
        )

    @staticmethod
    @transaction.atomic
    def archive_document(
        *,
        document,
        organization,
        archived_by,
    ):
        """
        Archive an employee document without
        deleting the database record or file.
        """

        if document.employee.organization_id != organization.id:
            raise ValueError(
                "Document does not belong to the organization."
            )

        if document.is_archived:
            raise ValueError(
                "Document is already archived."
            )

        document.is_archived = True
        document.archived_at = timezone.now()
        document.archived_by = archived_by

        document.save(
            update_fields=[
                "is_archived",
                "archived_at",
                "archived_by",
                "updated_at",
            ]
        )

        return document

    @staticmethod
    def list_archived_documents(
        *,
        employee,
    ):
        return (
            EmployeeDocument.objects
            .filter(
                employee=employee,
                is_archived=True,
            )
            .select_related(
                "archived_by",
            )
            .order_by(
                "-archived_at",
            )
        )

    @staticmethod
    @transaction.atomic
    def restore_document(
        *,
        document,
        organization,
    ):
        """
        Restore an archived employee document.
        """

        if document.employee.organization_id != organization.id:
            raise ValueError(
                "Document does not belong to the organization."
            )

        if not document.is_archived:
            raise ValueError(
                "Document is not archived."
            )

        document.is_archived = False
        document.archived_at = None
        document.archived_by = None

        document.save(
            update_fields=[
                "is_archived",
                "archived_at",
                "archived_by",
                "updated_at",
            ]
        )

        return document

    @staticmethod
    def get_archived_document(
        *,
        employee,
        document_id,
    ):
        return (
            EmployeeDocument.objects
            .select_related(
                "archived_by",
            )
            .get(
                id=document_id,
                employee=employee,
                is_archived=True,
            )
        )