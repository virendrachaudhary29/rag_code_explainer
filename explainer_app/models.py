from django.db import models

class CodeFile(models.Model):
    file = models.FileField(upload_to='code_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name
