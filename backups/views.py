# -*- coding: utf-8 -*-

from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template import RequestContext
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404, HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.utils.encoding import smart_str
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.db import connections
from django.core.paginator import InvalidPage, EmptyPage, Paginator
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.contrib import messages

from backups.models import Backup
from backups.forms import BackupForm
from backups.tasks import run_backup


@login_required
@staff_member_required
def backups_list(request):
    """Show the list of backups"""

    liste = Backup.objects.order_by('name').all()

    return render_to_response('backups/backups/list.html', {'liste': liste}, context_instance=RequestContext(request))


@login_required
@staff_member_required
def backups_show(request, pk):
    """Show details of a hostname forwarder"""

    object = get_object_or_404(Backup, pk=pk)

    liste = object.backuprun_set.order_by('-start_date').all()

    return render_to_response('backups/backups/show.html', {'object': object, 'liste': liste}, context_instance=RequestContext(request))


@login_required
@staff_member_required
def backups_edit(request, pk):
    """Edit a backup"""

    try:
        object = Backup.objects.get(pk=pk)
    except:
        object = Backup()

    if request.method == 'POST':  # If the form has been submitted...
        form = BackupForm(request.POST, instance=object)

        if form.is_valid():  # If the form is valid
            object = form.save()

            messages.success(request, 'The backup has been saved.')

            return redirect(reverse('backups.views.backups_list'))
    else:
        form = BackupForm(instance=object)

    return render_to_response('backups/backups/edit.html', {'form': form}, context_instance=RequestContext(request))


@login_required
@staff_member_required
def backups_delete(request, pk):
    """Delete a backup"""

    object = get_object_or_404(Backup, pk=pk)

    object.delete()

    messages.success(request, 'The backup has been deleted. The destination folder has not been removed !')

    return redirect(reverse('backups.views.backups_list', args=()))


@login_required
@staff_member_required
def backups_run(request, pk):
    """Run a backup"""

    object = get_object_or_404(Backup, pk=pk)

    run_backup.delay(object.pk)

    messages.success(request, 'The backup is running')

    return redirect(reverse('backups.views.backups_list', args=()))