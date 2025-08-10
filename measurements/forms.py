from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Goat


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class CustomUserRegistrationForm(UserCreationForm):
    """Simplified user registration form with only username and password"""
    
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Customize form field widgets
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter a strong password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })

    def clean_username(self):
        """Validate username"""
        username = self.cleaned_data.get('username')
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters long.")
        return username

    def save(self, commit=True):
        """Save the user"""
        user = super().save(commit=False)
        
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile"""
    
    organization = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'University, Farm, Research Institute'
        })
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        """Validate that email is unique (excluding current user)"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("A user with this email already exists.")
        return email


class MultipleImageUploadForm(forms.Form):
    """Form for uploading multiple images of the same goat"""
    
    goat = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        empty_label="Create new goat",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    goat_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter goat name for new goat'
        })
    )
    
    breed = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Boer, Saanen, Nubian'
        })
    )
    
    age_months = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=300,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Age in months'
        })
    )
    
    sex = forms.ChoiceField(
        choices=[('', 'Select sex'), ('M', 'Male'), ('F', 'Female')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    weight_kg = forms.DecimalField(
        required=False,
        min_value=0.1,
        max_value=200.0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Weight in kg',
            'step': '0.1'
        })
    )
    
    images = MultipleFileField(
        widget=MultipleFileInput(attrs={
            'accept': 'image/*',
            'class': 'form-control'
        }),
        help_text='Select multiple images of the same goat for better measurement accuracy',
        required=True
    )
    
    reference_length_cm = forms.DecimalField(
        required=False,
        min_value=0.1,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Reference object length',
            'step': '0.1'
        })
    )
    
    use_advanced_ai = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    session_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Optional: name for this measurement session'
        })
    )

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['goat'].queryset = Goat.objects.filter(owner=user).order_by('-created_at')

    def clean_images(self):
        """Validate uploaded images"""
        images = self.files.getlist('images')
        
        if not images:
            raise ValidationError('Please select at least one image.')
        
        if len(images) > 10:  # Limit to 10 images per batch
            raise ValidationError('Please select no more than 10 images at once.')
        
        # Validate each image
        max_size = 10 * 1024 * 1024  # 10MB per image
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        
        for image in images:
            if image.size > max_size:
                raise ValidationError(f'Image {image.name} is too large. Maximum size is 10MB.')
            
            if image.content_type not in allowed_types:
                raise ValidationError(f'Image {image.name} has unsupported format. Use JPEG, PNG, or WebP.')
        
        return images

    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        goat = cleaned_data.get('goat')
        goat_name = cleaned_data.get('goat_name')
        
        if not goat and not goat_name:
            raise ValidationError('Please either select an existing goat or provide a name for a new goat.')
        
        return cleaned_data


class BatchProcessingStatusForm(forms.Form):
    """Form for checking batch processing status"""
    
    session_id = forms.UUIDField(
        widget=forms.HiddenInput()
    )
