from datetime import date

from celery import shared_task

from django.db import transaction

from apps.organization.models import Organization

from .services import (
    LeaveAccrualService,
    LeaveBalanceService,
)

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={
        "max_retries": 5,
    },
)
def accrue_leave_for_organization(
    self,
    organization_id,
    year,
    month,
):
    organization = (
        Organization.objects.get(
            id=organization_id,
        )
    )

    accruals = (
        LeaveAccrualService
        .accrue_month(
            organization=organization,
            year=year,
            month=month,
        )
    )

    return {
        "organization_id": str(
            organization.id
        ),
        "year": year,
        "month": month,
        "created": len(accruals),
    }

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={
        "max_retries": 5,
    },
)
def accrue_leave_for_all_organizations(
    self,
    year,
    month,
):
    organizations = (
        Organization.objects
        .filter(
            is_active=True,
        )
        .values_list(
            "id",
            flat=True,
        )
    )

    queued = 0

    for organization_id in organizations:

        accrue_leave_for_organization.delay(
            str(
                organization_id
            ),
            year,
            month,
        )

        queued += 1

    return {
        "year": year,
        "month": month,
        "organizations_queued": queued,
    }


@shared_task
def accrue_leave_for_current_month():
    today = date.today()

    organizations = (
        Organization.objects
        .filter(
            is_active=True,
        )
        .values_list(
            "id",
            flat=True,
        )
    )

    queued = 0

    for organization_id in organizations:

        accrue_leave_for_organization.delay(
            str(organization_id),
            today.year,
            today.month,
        )

        queued += 1

    return {
        "year": today.year,
        "month": today.month,
        "organizations_queued": queued,
    }

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={
        "max_retries": 5,
    },
)
def initialize_leave_balances_for_organization(
    self,
    organization_id,
    year,
):
    organization = Organization.objects.get(
        id=organization_id,
        is_active=True,
    )

    balances = (
        LeaveBalanceService
        .initialize_year(
            organization=organization,
            year=year,
        )
    )

    return {
        "organization_id": str(
            organization.id
        ),
        "year": year,
        "balances_created": len(balances),
    }

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={
        "max_retries": 5,
    },
)
def initialize_leave_balances_for_organization(
    self,
    organization_id,
    year,
):
    organization = Organization.objects.get(
        id=organization_id,
        is_active=True,
    )

    balances = (
        LeaveBalanceService
        .initialize_year(
            organization=organization,
            year=year,
        )
    )

    return {
        "organization_id": str(
            organization.id
        ),
        "year": year,
        "balances_created": len(balances),
    }

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={
        "max_retries": 5,
    },
)
def initialize_leave_balances_for_all_organizations(
    self,
    year,
):
    organizations = (
        Organization.objects
        .filter(
            is_active=True,
        )
        .values_list(
            "id",
            flat=True,
        )
    )

    queued = 0

    for organization_id in organizations:

        initialize_leave_balances_for_organization.delay(
            str(organization_id),
            year,
        )

        queued += 1

    return {
        "year": year,
        "organizations_queued": queued,
    }

@shared_task
def initialize_leave_balances_for_current_year():

    today = date.today()

    return (
        initialize_leave_balances_for_all_organizations.delay(
            today.year,
        ).id
    )

@shared_task
def initialize_leave_balances_for_current_year():

    today = date.today()

    organizations = (
        Organization.objects
        .filter(
            is_active=True,
        )
        .values_list(
            "id",
            flat=True,
        )
    )

    queued = 0

    for organization_id in organizations:

        initialize_leave_balances_for_organization.delay(
            str(organization_id),
            today.year,
        )

        queued += 1

    return {
        "year": today.year,
        "organizations_queued": queued,
    }

@shared_task
def reconcile_current_year_leave_accruals():

    today = date.today()

    organizations = (
        Organization.objects
        .filter(
            is_active=True,
        )
        .values_list(
            "id",
            flat=True,
        )
    )

    queued = 0

    for organization_id in organizations:

        for month in range(
            1,
            today.month + 1,
        ):

            accrue_leave_for_organization.delay(
                str(organization_id),
                today.year,
                month,
            )

            queued += 1

    return {
        "year": today.year,
        "months_processed": today.month,
        "jobs_queued": queued,
    }