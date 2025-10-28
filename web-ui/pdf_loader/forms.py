from django import forms


class PdfUploadForm(forms.Form):
    """Form for uploading and configuring PDF ingestion"""

    RPG_SYSTEM_CHOICES = [
        ('DND_35', 'D&D 3.5'),
        ('PATHFINDER_1E', 'Pathfinder 1e'),
        ('PATHFINDER_2E', 'Pathfinder 2e'),
    ]

    PUBLICATION_TYPE_CHOICES = [
        ('CORE_RULEBOOK', 'Core Rulebook'),
        ('BESTIARY', 'Bestiary'),
        ('SUPPLEMENT', 'Supplement'),
        ('ADVENTURE', 'Adventure'),
        ('SETTING', 'Setting'),
    ]

    # Server configuration
    server_address = forms.CharField(
        max_length=255,
        initial='localhost',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'localhost'
        }),
        label='Server Address'
    )

    server_port = forms.IntegerField(
        initial=50051,
        min_value=1,
        max_value=65535,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '50051'
        }),
        label='Server Port'
    )

    # PDF file and metadata
    pdf_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf'
        }),
        label='PDF File'
    )

    pdf_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Monster Manual, Core Rulebook'
        }),
        label='PDF Name'
    )

    rpg_system = forms.ChoiceField(
        choices=RPG_SYSTEM_CHOICES,
        initial='PATHFINDER_1E',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='RPG System'
    )

    publication_type = forms.ChoiceField(
        choices=PUBLICATION_TYPE_CHOICES,
        initial='BESTIARY',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Publication Type'
    )

    # Chunking parameters
    chunk_size = forms.IntegerField(
        initial=600,
        min_value=100,
        max_value=2000,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '600'
        }),
        label='Chunk Size',
        help_text='100-2000'
    )

    chunk_overlap = forms.IntegerField(
        initial=50,
        min_value=0,
        max_value=500,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '50'
        }),
        label='Chunk Overlap',
        help_text='0-500'
    )

    def clean_pdf_file(self):
        """Validate PDF file"""
        pdf_file = self.cleaned_data.get('pdf_file')

        if pdf_file:
            # Check file extension
            if not pdf_file.name.endswith('.pdf'):
                raise forms.ValidationError('File must be a PDF')

            # Check file size (max 50MB)
            if pdf_file.size > 50 * 1024 * 1024:
                raise forms.ValidationError('File size must be less than 50MB')

        return pdf_file
