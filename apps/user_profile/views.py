from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .forms import UserSettingsForm


@login_required
def settings(request):
    if request.method == 'POST':
        form = UserSettingsForm(request.POST, instance=request.user.settings)
        if form.is_valid():
            form.save()
    else:
        form = UserSettingsForm(instance=request.user.settings)
    return render(request, 'core/form_template.html', {'form': form})
