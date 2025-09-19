from django import forms

from .models import Client, Mailing, Message


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["email", "full_name", "comment"]


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["subject", "body"]


class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ["first_send_time", "end_time", "message", "clients"]

    def __init__(self, *args, **kwargs):

        self.owner_id = kwargs.pop("owner_id", None)
        super(MailingForm, self).__init__(*args, **kwargs)
        if self.owner_id:

            self.fields["message"].queryset = self.fields["message"].queryset.filter(
                owner_id=self.owner_id
            )
            self.fields["clients"].queryset = self.fields["clients"].queryset.filter(
                owner_id=self.owner_id
            )
