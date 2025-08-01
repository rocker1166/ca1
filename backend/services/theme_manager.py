from pptx.dml.color import RGBColor

class ThemeManager:
    """Manages presentation themes and color schemes"""
    
    THEMES = {
        "professional": {
            "primary": RGBColor(44, 62, 80),      # Dark blue
            "secondary": RGBColor(52, 152, 219),  # Blue
            "accent": RGBColor(231, 76, 60),      # Red
            "background": RGBColor(255, 255, 255), # White
            "text": RGBColor(0, 0, 0),            # Black
            "title_font": "Calibri",
            "body_font": "Calibri",
        },
        "academic": {
            "primary": RGBColor(50, 50, 50),      # Dark gray
            "secondary": RGBColor(0, 103, 120),   # Teal
            "accent": RGBColor(170, 55, 55),      # Burgundy
            "background": RGBColor(255, 255, 255), # White
            "text": RGBColor(0, 0, 0),            # Black
            "title_font": "Georgia",
            "body_font": "Calibri",
        },
        "science": {
            "primary": RGBColor(21, 67, 96),      # Dark blue
            "secondary": RGBColor(41, 128, 185),  # Medium blue
            "accent": RGBColor(46, 204, 113),     # Green
            "background": RGBColor(255, 255, 255), # White
            "text": RGBColor(0, 0, 0),            # Black
            "title_font": "Arial",
            "body_font": "Arial",
        },
        "humanities": {
            "primary": RGBColor(110, 44, 0),      # Brown
            "secondary": RGBColor(212, 172, 13),  # Gold
            "accent": RGBColor(120, 40, 140),     # Purple
            "background": RGBColor(252, 250, 242), # Off-white
            "text": RGBColor(30, 30, 30),         # Near-black
            "title_font": "Garamond",
            "body_font": "Georgia",
        },
        "engineering": {
            "primary": RGBColor(52, 73, 94),      # Dark gray-blue
            "secondary": RGBColor(243, 156, 18),  # Orange
            "accent": RGBColor(39, 174, 96),      # Green
            "background": RGBColor(255, 255, 255), # White
            "text": RGBColor(0, 0, 0),            # Black
            "title_font": "Franklin Gothic",
            "body_font": "Arial",
        },
        "creative": {
            "primary": RGBColor(142, 68, 173),    # Purple
            "secondary": RGBColor(26, 188, 156),  # Teal
            "accent": RGBColor(241, 196, 15),     # Yellow
            "background": RGBColor(255, 255, 255), # White
            "text": RGBColor(0, 0, 0),            # Black
            "title_font": "Century Gothic",
            "body_font": "Segoe UI",
        }
    }
    
    @staticmethod
    def get_theme_colors(theme_name="professional"):
        """Get colors for specified theme"""
        if theme_name in ThemeManager.THEMES:
            return ThemeManager.THEMES[theme_name]
        return ThemeManager.THEMES["professional"]  # Default
    
    @staticmethod
    def suggest_theme_for_subject(subject_area):
        """Suggest appropriate theme based on subject area"""
        subject_theme_map = {
            "mathematics": "academic",
            "computer_science": "professional",
            "biology": "science",
            "chemistry": "science",
            "physics": "science",
            "history": "humanities",
            "literature": "humanities",
            "engineering": "engineering",
            "art": "creative",
            "design": "creative"
        }
        
        return subject_theme_map.get(subject_area, "professional")
