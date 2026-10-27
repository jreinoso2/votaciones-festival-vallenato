from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect


# Registro de usuarios con el formulario que trae Django
def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)  # queda con la sesión iniciada
            messages.success(request, 'Registro exitoso. Bienvenido ' + usuario.username)
            return redirect('inicio')
    else:
        form = UserCreationForm()
    return render(request, 'usuarios/registro.html', {'form': form})
