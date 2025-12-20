from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def subscription_required(plan_names):
    """
    Decorador para restringir acceso a vistas según el plan de suscripción.
    plan_names puede ser una lista de nombres de planes permitidos (ej: ['PRO', 'PREMIUM'])
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            suscripcion = getattr(request.user, 'suscripcion', None)
            
            # Si no tiene suscripción, redirigir a planes
            if not suscripcion or not suscripcion.es_valida:
                messages.warning(request, "Necesitas una suscripción activa para acceder a esta función.")
                return redirect('usuarios:lista_planes')
            
            # Verificar si el plan del usuario está en los permitidos
            # Nota: Asumimos que los planes superiores incluyen los inferiores si se pasa la lista completa
            # O podemos implementar lógica de jerarquía. Por ahora, lista explícita.
            if suscripcion.plan.nombre not in plan_names:
                messages.warning(request, f"Esta función requiere un plan superior. Tu plan actual es {suscripcion.plan.nombre}.")
                return redirect('usuarios:lista_planes')
                
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
