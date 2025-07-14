from django.db import models


class TitleSuggestionRequest(models.Model):
    """
    Model to store title suggestion requests, content, and suggested titles.
    """
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Store suggested titles as a comma-separated string
    suggested_titles = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Title Suggestion Request {self.id}"
    
    def get_suggested_titles_list(self):
        """
        Return suggested titles as a list
        """
        if not self.suggested_titles:
            return []
        return [title.strip() for title in self.suggested_titles.split('|||')]
    
    def set_suggested_titles_list(self, titles_list):
        """
        Convert a list of titles to a string for storage
        """
        if not titles_list:
            self.suggested_titles = None
        else:
            self.suggested_titles = '|||'.join(titles_list)