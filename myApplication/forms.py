from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from .models import ProcesVerbal, ResultatCandidat, User


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


class ProcesVerbalForm(forms.ModelForm):
    """Formulaire de saisie du procès-verbal global"""
    
    nombre_inscrits = forms.IntegerField(
        required=True,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-green-500 focus:border-transparent transition duration-200',
            'placeholder': 'Nombre d\'inscrits dans ce bureau',
            'min': '0',
            'id': 'id_nombre_inscrits_bureau',
            'required': 'required'
        }),
        label='Nombre d\'inscrits dans ce bureau',
        help_text='Nombre total d\'électeurs inscrits dans ce bureau de vote'
    )
    
    class Meta:
        model = ProcesVerbal
        fields = ['nombre_votants', 'bulletins_nuls', 'bulletins_blancs', 'photo_pv', 'observations']
        widgets = {
            'nombre_votants': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-green-500 focus:border-transparent transition duration-200',
                'placeholder': 'Nombre de votants effectifs',
                'min': '0',
                'id': 'id_nombre_votants',
                'required': 'required'
            }),
            'bulletins_nuls': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-green-500 focus:border-transparent transition duration-200',
                'placeholder': 'Nombre de bulletins nuls',
                'min': '0',
                'value': '0',
                'id': 'id_bulletins_nuls'
            }),
            'bulletins_blancs': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-green-500 focus:border-transparent transition duration-200',
                'placeholder': 'Nombre de bulletins blancs',
                'min': '0',
                'value': '0',
                'id': 'id_bulletins_blancs'
            }),
            'photo_pv': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-green-500 focus:border-transparent transition duration-200',
                'accept': 'image/*',
                'capture': 'environment'
            }),
            'observations': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-green-500 focus:border-transparent transition duration-200',
                'placeholder': 'Observations ou remarques (optionnel)',
                'rows': 3
            })
        }
        labels = {
            'nombre_votants': 'Nombre de votants effectifs',
            'bulletins_nuls': 'Bulletins nuls',
            'bulletins_blancs': 'Bulletins blancs',
            'photo_pv': 'Photo du procès-verbal',
            'observations': 'Observations'
        }
    
    def __init__(self, *args, **kwargs):
        self.bureau_vote = kwargs.pop('bureau_vote', None)
        super().__init__(*args, **kwargs)
        
        # Définir les valeurs par défaut pour les champs si aucune instance n'existe
        if not self.instance.pk:
            self.fields['bulletins_nuls'].initial = 0
            self.fields['bulletins_blancs'].initial = 0
            # Pré-remplir avec le nombre d'inscrits du bureau si disponible
            if self.bureau_vote and self.bureau_vote.nombre_inscrits > 0:
                self.fields['nombre_inscrits'].initial = self.bureau_vote.nombre_inscrits
        else:
            # Si on modifie, charger le nombre d'inscrits actuel du bureau
            if self.bureau_vote:
                self.fields['nombre_inscrits'].initial = self.bureau_vote.nombre_inscrits
    
    def clean_nombre_inscrits(self):
        nombre_inscrits = self.cleaned_data.get('nombre_inscrits')
        
        if nombre_inscrits is None:
            raise ValidationError("Ce champ est obligatoire.")
        
        if nombre_inscrits <= 0:
            raise ValidationError("Le nombre d'inscrits doit être supérieur à zéro.")
        
        return nombre_inscrits
    
    def clean_nombre_votants(self):
        nombre_votants = self.cleaned_data.get('nombre_votants')
        
        if nombre_votants is None:
            raise ValidationError("Ce champ est obligatoire.")
        
        if nombre_votants < 0:
            raise ValidationError("Le nombre de votants ne peut pas être négatif.")
        
        return nombre_votants
    
    def clean_bulletins_nuls(self):
        bulletins_nuls = self.cleaned_data.get('bulletins_nuls')
        
        if bulletins_nuls is None:
            return 0
        
        if bulletins_nuls < 0:
            raise ValidationError("Le nombre de bulletins nuls ne peut pas être négatif.")
        
        return bulletins_nuls
    
    def clean_bulletins_blancs(self):
        bulletins_blancs = self.cleaned_data.get('bulletins_blancs')
        
        if bulletins_blancs is None:
            return 0
        
        if bulletins_blancs < 0:
            raise ValidationError("Le nombre de bulletins blancs ne peut pas être négatif.")
        
        return bulletins_blancs
    
    def clean(self):
        cleaned_data = super().clean()
        nombre_inscrits = cleaned_data.get('nombre_inscrits', 0)
        nombre_votants = cleaned_data.get('nombre_votants', 0)
        bulletins_nuls = cleaned_data.get('bulletins_nuls', 0)
        bulletins_blancs = cleaned_data.get('bulletins_blancs', 0)
        
        # S'assurer que les valeurs ne sont pas None
        if nombre_inscrits is None:
            nombre_inscrits = 0
        if nombre_votants is None:
            nombre_votants = 0
        if bulletins_nuls is None:
            bulletins_nuls = 0
        if bulletins_blancs is None:
            bulletins_blancs = 0
        
        # Vérifier que le nombre de votants ne dépasse pas les inscrits
        if nombre_votants > nombre_inscrits:
            raise ValidationError(
                f"Le nombre de votants ({nombre_votants}) ne peut pas dépasser "
                f"le nombre d'inscrits ({nombre_inscrits})."
            )
        
        # Vérifier que nuls + blancs <= votants
        if (bulletins_nuls + bulletins_blancs) > nombre_votants:
            raise ValidationError(
                f"La somme des bulletins nuls ({bulletins_nuls}) et blancs ({bulletins_blancs}) "
                f"ne peut pas dépasser le nombre de votants ({nombre_votants})."
            )
        
        return cleaned_data
    
    def clean_photo_pv(self):
        photo = self.cleaned_data.get('photo_pv')
        
        if photo:
            # Vérifier la taille du fichier (max 10MB)
            if photo.size > 10 * 1024 * 1024:
                raise ValidationError("La taille de l'image ne doit pas dépasser 10 MB.")
            
            # Vérifier le type de fichier
            if not photo.content_type.startswith('image/'):
                raise ValidationError("Le fichier doit être une image.")
        
        return photo


class ResultatCandidatFormSet(forms.BaseFormSet):
    """FormSet personnalisé pour la validation globale des résultats"""
    
    def __init__(self, *args, **kwargs):
        self.proces_verbal = kwargs.pop('proces_verbal', None)
        self.suffrages_exprimes = kwargs.pop('suffrages_exprimes', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        """Vérifie que la somme des voix = suffrages exprimés"""
        if any(self.errors):
            return
        
        total_voix = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                nombre_voix = form.cleaned_data.get('nombre_voix', 0)
                # S'assurer que nombre_voix n'est pas None
                if nombre_voix is None:
                    nombre_voix = 0
                total_voix += nombre_voix
        
        if self.suffrages_exprimes is not None and total_voix != self.suffrages_exprimes:
            raise ValidationError(
                f"La somme des voix ({total_voix}) doit être égale aux suffrages exprimés ({self.suffrages_exprimes}). "
                f"Différence : {abs(total_voix - self.suffrages_exprimes)} voix."
            )


class ResultatCandidatForm(forms.ModelForm):
    """Formulaire pour la saisie des voix d'un candidat"""
    
    class Meta:
        model = ResultatCandidat
        fields = ['nombre_voix']
        widgets = {
            'nombre_voix': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200',
                'min': '0',
                'placeholder': '0',
                'value': '0'
            })
        }
        labels = {
            'nombre_voix': ''
        }
    
    def __init__(self, *args, **kwargs):
        self.candidat = kwargs.pop('candidat', None)
        super().__init__(*args, **kwargs)
        
        # Définir la valeur par défaut à 0
        if not self.instance.pk:
            self.fields['nombre_voix'].initial = 0
    
    def clean_nombre_voix(self):
        nombre_voix = self.cleaned_data.get('nombre_voix')
        
        # Si la valeur est None, retourner 0
        if nombre_voix is None:
            return 0
        
        if nombre_voix < 0:
            raise ValidationError("Le nombre de voix ne peut pas être négatif.")
        
        return nombre_voix