from django import forms
from .models import CodeFile

class CodeFileForm(forms.ModelForm):
    class Meta:
        model = CodeFile
        fields = ['file']
