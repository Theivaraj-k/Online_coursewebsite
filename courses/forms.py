from django import forms
from .models import Course, Module, Content, Review

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'category', 'description', 'price', 'discount_price', 'thumbnail', 'is_published']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['title', 'description', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class TextContentForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = ['title', 'text_content', 'is_preview', 'order']
        widgets = {
            'text_content': forms.Textarea(attrs={'rows': 10, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        self.fields['is_preview'].widget.attrs.update({'class': 'form-check-input'})

class VideoContentForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = ['title', 'video_url', 'video_file', 'is_preview', 'order']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'video_file':
                self.fields[field].widget.attrs.update({'class': 'form-control'})
        self.fields['is_preview'].widget.attrs.update({'class': 'form-check-input'})

class PDFContentForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = ['title', 'pdf_file', 'is_preview', 'order']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'pdf_file':
                self.fields[field].widget.attrs.update({'class': 'form-control'})
        self.fields['is_preview'].widget.attrs.update({'class': 'form-check-input'})

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['comment'].widget.attrs.update({'class': 'form-control'})
        self.fields['rating'].widget.attrs.update({'class': 'form-select'})