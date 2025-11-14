from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Resultat, User


class LoginForm(AuthenticationForm):
    """Formulaire de connexion personnalisé"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200',
            'placeholder': "Nom d'utilisateur"
        }),
        label="Nom d'utilisateur"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200',
            'placeholder': 'Mot de passe'
        }),
        label="Mot de passe"
    )


class ResultatForm(forms.ModelForm):
    """Formulaire de saisie des résultats"""
    
    class Meta:
        model = Resultat
        fields = ['nombre_voix', 'photo_pv', 'observations']
        widgets = {
            'nombre_voix': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-green-500 focus:border-transparent transition duration-200',
                'placeholder': 'Nombre de voix obtenues',
                'min': '0'
            }),
            'photo_pv': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-green-500 focus:border-transparent transition duration-200',
                'accept': 'image/*',
                'capture': 'environment'  # Pour ouvrir directement la caméra sur mobile
            }),
            'observations': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-green-500 focus:border-transparent transition duration-200',
                'placeholder': 'Observations (optionnel)',
                'rows': 3
            })
        }
        labels = {
            'nombre_voix': 'Nombre de voix',
            'photo_pv': 'Photo du procès-verbal',
            'observations': 'Observations'
        }
    
    def __init__(self, *args, **kwargs):
        self.bureau_vote = kwargs.pop('bureau_vote', None)
        self.candidat = kwargs.pop('candidat', None)
        super().__init__(*args, **kwargs)
    
    def clean_nombre_voix(self):
        nombre_voix = self.cleaned_data.get('nombre_voix')
        
        if nombre_voix is not None and nombre_voix < 0:
            raise forms.ValidationError("Le nombre de voix ne peut pas être négatif.")
        
        if self.bureau_vote and nombre_voix > self.bureau_vote.nombre_inscrits:
            raise forms.ValidationError(
                f"Le nombre de voix ({nombre_voix}) ne peut pas dépasser "
                f"le nombre d'inscrits ({self.bureau_vote.nombre_inscrits}) dans ce bureau."
            )
        
        return nombre_voix
    
    def clean_photo_pv(self):
        photo = self.cleaned_data.get('photo_pv')
        
        if photo:
            # Vérifier la taille du fichier (max 5MB)
            if photo.size > 5 * 1024 * 1024:
                raise forms.ValidationError("La taille de l'image ne doit pas dépasser 5 MB.")
            
            # Vérifier le type de fichier
            if not photo.content_type.startswith('image/'):
                raise forms.ValidationError("Le fichier doit être une image.")
        
        return photo