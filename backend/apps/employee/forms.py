from django import forms

from .models import (
    EmployeeIdentity,
    EmployeeContact,
    EmployeeAssignment,
    Employment,
    EmployeeDocument,
)

class EmployeeDocumentUploadForm(forms.ModelForm):

    class Meta:
        model = EmployeeDocument

        fields = [
            "document_type",
            "name",
            "file",
            "description",
            "issue_date",
            "expiry_date",
        ]

        widgets = {
            "document_type": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Document name",
                }
            ),

            "file": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Optional description",
                }
            ),

            "issue_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "expiry_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
        }

class EmployeeIdentityForm(forms.ModelForm):

    class Meta:
        model = EmployeeIdentity
        fields = [
            "first_name",
            "middle_name",
            "last_name",
            "date_of_birth",
            "gender",
        ]

        widgets = {
            "date_of_birth": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),
        }


class EmployeeContactForm(forms.ModelForm):

    class Meta:
        model = EmployeeContact
        fields = [
            "personal_email",
            "company_email",
            "phone_number",
            "address",
        ]


class EmployeeEmploymentForm(forms.ModelForm):

    class Meta:
        model = Employment
        fields = [
            "employment_type",
            "employment_status",
            "offer_date",
            "employment_start_date",
            "probation_end_date",
            "confirmation_status",
            "confirmation_date",
            "date_left",
        ]

        widgets = {
            "offer_date": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),
            "employment_start_date": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),
            "probation_end_date": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),
            "confirmation_date": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),
            "date_left": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),
        }