from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import ClientForm, MailingForm, MessageForm
from .models import Client, Mailing, MailingAttempt, Message
from .services import send_mailing


def home(request):
    cache_key = "home_stats_general"

    cached_stats = cache.get(cache_key)

    if cached_stats is None:

        total_mailings = Mailing.objects.count()
        active_mailings = Mailing.objects.filter(status="running").count()
        unique_clients = Client.objects.count()

        context = {
            "total_mailings": total_mailings,
            "active_mailings": active_mailings,
            "unique_clients": unique_clients,
        }

        cache.set(cache_key, context, 900)
        print("Статистика вычислена и сохранена в кеш")
    else:
        context = cached_stats
        print("Статистика получена из кеша")

    return render(request, "mailing/home.html", context)


class OwnerRequiredMixin:
    """
    Mixin для фильтрации queryset по владельцу (текущему пользователю).
    """

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(owner=self.request.user)


class ClientListView(LoginRequiredMixin, OwnerRequiredMixin, ListView):
    model = Client
    template_name = "mailing/client_list.html"
    context_object_name = "clients"
    login_url = "users:login"


class ClientDetailView(LoginRequiredMixin, OwnerRequiredMixin, DetailView):
    model = Client
    template_name = "mailing/client_detail.html"
    context_object_name = "client"
    login_url = "users:login"


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = "mailing/client_form.html"
    success_url = reverse_lazy("mailing:client_list")
    login_url = "users:login"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ClientUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = "mailing/client_form.html"
    success_url = reverse_lazy("mailing:client_list")
    login_url = "users:login"


class ClientDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Client
    template_name = "mailing/client_confirm_delete.html"
    success_url = reverse_lazy("mailing:client_list")
    login_url = "users:login"


class MessageListView(LoginRequiredMixin, OwnerRequiredMixin, ListView):
    model = Message
    template_name = "mailing/message_list.html"
    context_object_name = "messages"
    login_url = "users:login"


class MessageDetailView(LoginRequiredMixin, OwnerRequiredMixin, DetailView):
    model = Message
    template_name = "mailing/message_detail.html"
    context_object_name = "message"
    login_url = "users:login"


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = "mailing/message_form.html"
    success_url = reverse_lazy("mailing:message_list")
    login_url = "users:login"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = "mailing/message_form.html"
    success_url = reverse_lazy("mailing:message_list")
    login_url = "users:login"


class MessageDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Message
    template_name = "mailing/message_confirm_delete.html"
    success_url = reverse_lazy("mailing:message_list")
    login_url = "users:login"


class MailingListView(LoginRequiredMixin, ListView):  # Для всех или с проверкой прав
    model = Mailing
    template_name = "mailing/mailing_list.html"
    context_object_name = "mailings"
    login_url = "users:login"

    def get_queryset(self):
        user = self.request.user

        if user.has_perm("mailing.view_mailing_list"):

            return Mailing.objects.all()
        else:

            return Mailing.objects.filter(owner=user)


class MailingDetailView(LoginRequiredMixin, OwnerRequiredMixin, DetailView):
    model = Mailing
    template_name = "mailing/mailing_detail.html"
    context_object_name = "mailing"
    login_url = "users:login"


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailing/mailing_form.html"
    success_url = reverse_lazy("mailing:mailing_list")
    login_url = "users:login"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["owner_id"] = self.request.user.id
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MailingUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailing/mailing_form.html"
    success_url = reverse_lazy("mailing:mailing_list")
    login_url = "users:login"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["owner_id"] = self.request.user.id
        return kwargs


class MailingDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Mailing
    template_name = "mailing/mailing_confirm_delete.html"
    success_url = reverse_lazy("mailing:mailing_list")
    login_url = "users:login"


class MailingAttemptListView(LoginRequiredMixin, ListView):
    model = MailingAttempt
    template_name = "mailing/attempt_list.html"
    context_object_name = "attempts"
    login_url = "users:login"

    def get_queryset(self):
        user = self.request.user
        if user.has_perm("mailing.view_mailing_list"):

            return MailingAttempt.objects.all()
        else:

            return MailingAttempt.objects.filter(mailing__owner=user)


class MailingStatisticsView(LoginRequiredMixin, ListView):
    model = Mailing
    template_name = "mailing/statistics.html"
    context_object_name = "mailings"
    login_url = "users:login"

    def get_queryset(self):
        user = self.request.user
        if user.has_perm("mailing.view_mailing_list"):

            queryset = Mailing.objects.all()
        else:

            queryset = Mailing.objects.filter(owner=user)

        queryset = queryset.annotate(
            total_attempts=Count("mailingattempt"),
            successful_attempts=Count(
                "mailingattempt", filter=Q(mailingattempt__status="success")
            ),
            failed_attempts=Count(
                "mailingattempt", filter=Q(mailingattempt__status="failed")
            ),
        )
        return queryset


@login_required
def send_mailing_view(request, mailing_id):
    mailing = get_object_or_404(Mailing, id=mailing_id, owner=request.user)

    if not (
        mailing.owner == request.user
        or request.user.has_perm("mailing.set_mailing_status")
    ):
        messages.error(request, "У вас нет прав для отправки этой рассылки.")
        return redirect("mailing:mailing_list")

    if request.method == "POST":
        success = send_mailing(mailing_id)
        if success:
            messages.success(request, f"Рассылка {mailing_id} успешно отправлена.")
        else:
            messages.error(request, f"Ошибка при отправке рассылки {mailing_id}.")
        return redirect("mailing:mailing_detail", pk=mailing_id)

    return render(request, "mailing/send_mailing_confirm.html", {"mailing": mailing})
