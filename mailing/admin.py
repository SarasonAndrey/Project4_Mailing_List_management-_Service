from django.contrib import admin

from .models import Client, Mailing, MailingAttempt, Message


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name")
    search_fields = ("email", "full_name")
    list_filter = ("full_name",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "body")
    search_fields = ("subject", "body")


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ("id", "first_send_time", "end_time", "status", "message")
    list_filter = ("status", "first_send_time")


@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "attempt_time", "status", "mailing")
    list_filter = ("status", "attempt_time")
    readonly_fields = ("attempt_time", "status", "server_response", "mailing")
