"""
Utility module to extract identifiers from message content.
"""

import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag

# Download necessary NLTK resources (uncomment if needed)
# nltk.download('punkt')
# nltk.download('averaged_perceptron_tagger')
# nltk.download('maxent_ne_chunker')
# nltk.download('words')

class IdentifierExtractor:
    """
    Utility class to extract identifiers from message content.
    Identifiers include email addresses, person names, company names, 
    project names, technical terms, and important keywords.
    """
    
    def __init__(self):
        """Initialize the IdentifierExtractor."""
        # Common project names and technical terms to look for
        self.project_keywords = [
            "project", "projectx", "project x", "dashboard", "infrastructure",
            "ui", "ux", "frontend", "backend", "deploy", "deployment",
            "feature", "component", "layout", "testing", "compliance"
        ]
        
        # Email pattern for regex matching
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        # Mention pattern (e.g., @username)
        self.mention_pattern = r'@\w+'
    
    def extract_email_addresses(self, text):
        """Extract email addresses from text."""
        return re.findall(self.email_pattern, text)
    
    def extract_mentions(self, text):
        """Extract @mentions from text."""
        return re.findall(self.mention_pattern, text)
    
    def extract_named_entities(self, text):
        """Extract named entities (person names, company names) from text."""
        tokens = word_tokenize(text)
        pos_tags = pos_tag(tokens)
        
        # Extract proper nouns (potential names)
        proper_nouns = [word for word, pos in pos_tags 
                       if pos.startswith('NNP') and len(word) > 1]
        
        return proper_nouns
    
    def extract_project_keywords(self, text):
        """Extract project names and technical terms."""
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in self.project_keywords:
            if keyword in text_lower:
                # Get the actual case from the original text
                start_idx = text_lower.find(keyword)
                if start_idx != -1:
                    end_idx = start_idx + len(keyword)
                    actual_word = text[start_idx:end_idx]
                    found_keywords.append(actual_word)
        
        return found_keywords
    
    def extract_all_identifiers(self, text):
        """
        Extract all types of identifiers from the text.
        
        Returns:
            A dictionary mapping identifier types to lists of identifiers.
        """
        emails = self.extract_email_addresses(text)
        mentions = self.extract_mentions(text)
        entities = self.extract_named_entities(text)
        keywords = self.extract_project_keywords(text)
        
        # Remove duplicates while preserving order
        all_identifiers = []
        added = set()
        
        for identifier in emails + mentions + entities + keywords:
            if identifier.lower() not in added:
                all_identifiers.append(identifier)
                added.add(identifier.lower())
        
        return {
            "all": all_identifiers,
            "emails": emails,
            "mentions": mentions,
            "entities": entities,
            "keywords": keywords
        }


if __name__ == "__main__":
    # Test the identifier extractor
    test_text = "Hey team, I've pushed the latest UI updates for ProjectX. Please contact john.doe@example.com for any issues. @samhill, let me know if it looks good from the QA perspective!"
    
    extractor = IdentifierExtractor()
    identifiers = extractor.extract_all_identifiers(test_text)
    
    print("All identifiers:", identifiers["all"])
    print("Emails:", identifiers["emails"])
    print("Mentions:", identifiers["mentions"])
    print("Named entities:", identifiers["entities"])
    print("Project keywords:", identifiers["keywords"]) 