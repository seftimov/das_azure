from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms


class SignupUserForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username'
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Email'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })

    username = forms.CharField(widget=forms.TextInput)
    email = forms.EmailField(widget=forms.EmailInput)
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class CoinFilterForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    currency = forms.ChoiceField(
        choices=[
            ('USD', 'USD'),
            ('EUR', 'EUR'),
            ('MKD', 'MKD')
        ],
        required=False,
        initial='USD',
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class OnchainSentimentForm(forms.Form):
    symbol = forms.ChoiceField(
        label="Coin",
        required=True,
        widget=forms.Select(attrs={
            "class": "form-select"
        })
    )

    start_date = forms.DateField(
        label="Start date",
        required=False,
        widget=forms.DateInput(attrs={
            "type": "date",
            "class": "form-control"
        })
    )

    end_date = forms.DateField(
        label="End date",
        required=False,
        widget=forms.DateInput(attrs={
            "type": "date",
            "class": "form-control"
        })
    )

    only_with_news = forms.BooleanField(
        label="Show only rows with news",
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            "class": "form-check-input"
        })
    )
