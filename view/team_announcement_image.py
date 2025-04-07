"""
Team Announcement Image Generator Module

This module provides functionality to generate visual team announcements for esports matches.
It creates stylized images showing team matchups with player information and role assignments.

Features:
- Creates visually appealing team matchup images
- Downloads required fonts if not available
- Highlights role matchups between teams
- Uses KSU Esports Tournament logo as centerpiece
- Supports different color coding for roles
"""

import os
from PIL import Image, ImageDraw, ImageFont
import pathlib
from config import settings
import json

# Define file paths for resources
BASE_DIR = pathlib.Path(__file__).parent.parent
LOGO_PATH = BASE_DIR / "common" / "images" / "KSU _Esports_Tournament.png"
FONTS_DIR = BASE_DIR / "view" / "fonts"
OUTPUT_DIR = BASE_DIR / "temp"

# Try to ensure directories exist, but don't fail if we can't create them
try:
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Create fonts directory if it doesn't exist
    os.makedirs(FONTS_DIR, exist_ok=True)
except (PermissionError, OSError) as e:
    print(f"Warning: Could not create required directories: {e}")
    # Use a temporary directory that should be writable
    import tempfile
    OUTPUT_DIR = pathlib.Path(tempfile.gettempdir())

# Default font paths - these will be checked and downloaded if needed
DEFAULT_BOLD_FONT = FONTS_DIR / "Roboto-Bold.ttf"
DEFAULT_REGULAR_FONT = FONTS_DIR / "Roboto-Regular.ttf"

# Color definitions - more professional palette
TEAM1_COLOR = (65, 105, 225)      # Royal Blue
TEAM2_COLOR = (220, 20, 60)       # Crimson
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GRAY = (180, 180, 180)
LIGHT_GRAY = (220, 220, 220)
DARK_GRAY = (40, 40, 40)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)

# Background gradient colors
BACKGROUND_TOP = (15, 15, 25)      # Dark blue-black
BACKGROUND_BOTTOM = (40, 40, 60)   # Slightly lighter blue-black

# Role colors - more vibrant professional colors
ROLE_COLORS = {
    "top": (220, 55, 55),           # Refined red
    "jungle": (50, 180, 80),        # Forest green
    "mid": (255, 200, 40),          # Golden yellow
    "bottom": (40, 120, 240),       # Deep blue
    "support": (170, 60, 220),      # Royal purple
    "tbd": (180, 180, 180),         # Gray
    "forced": (40, 40, 40)          # Dark gray
}

def download_fonts():
    """Check for fonts and use fallback if they don't exist"""
    # First check if the Roboto fonts are already on the system
    try:
        # Common system locations for Roboto fonts
        system_locations = [
            # macOS
            "/Library/Fonts/Roboto-Bold.ttf",
            "/Library/Fonts/Roboto-Regular.ttf",
            "/System/Library/Fonts/Roboto-Bold.ttf",
            "/System/Library/Fonts/Roboto-Regular.ttf",
            # User fonts on macOS
            f"{os.path.expanduser('~')}/Library/Fonts/Roboto-Bold.ttf",
            f"{os.path.expanduser('~')}/Library/Fonts/Roboto-Regular.ttf",
            # Linux
            "/usr/share/fonts/truetype/roboto/Roboto-Bold.ttf",
            "/usr/share/fonts/truetype/roboto/Roboto-Regular.ttf",
            # Windows
            "C:/Windows/Fonts/Roboto-Bold.ttf",
            "C:/Windows/Fonts/Roboto-Regular.ttf",
        ]
        
        # Check if we can find system fonts
        for path in system_locations:
            if os.path.exists(path) and "Bold" in path:
                global DEFAULT_BOLD_FONT
                DEFAULT_BOLD_FONT = path
            elif os.path.exists(path) and "Regular" in path:
                global DEFAULT_REGULAR_FONT
                DEFAULT_REGULAR_FONT = path
        
        # If we found system fonts, return
        if (isinstance(DEFAULT_BOLD_FONT, str) and isinstance(DEFAULT_REGULAR_FONT, str) and 
            os.path.exists(DEFAULT_BOLD_FONT) and os.path.exists(DEFAULT_REGULAR_FONT)):
            print(f"Using system fonts: {DEFAULT_BOLD_FONT} and {DEFAULT_REGULAR_FONT}")
            return True

        # At this point, we don't have system fonts or our own fonts
        print("No suitable fonts found, using default")
        return False
    except Exception as e:
        print(f"Error finding fonts: {e}")
        return False

def get_role_icon(role):
    """Return a text representation of the role icon"""
    role = role.lower()
    icon_map = {
        "top": "🟥",
        "jungle": "🟩",
        "mid": "🟨",
        "bottom": "🟦",
        "support": "🟪",
        "tbd": "⬜",
        "forced": "⬛"
    }
    return icon_map.get(role, "⬜")

def create_gradient_background(width, height, top_color, bottom_color):
    """
    Creates a gradient background image
    
    Args:
        width: Image width
        height: Image height
        top_color: RGB color tuple for top
        bottom_color: RGB color tuple for bottom
        
    Returns:
        Image: PIL image with gradient background
    """
    # Create a new image
    bg = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(bg)
    
    # Draw gradient (divide into multiple bands for smoother gradient)
    num_bands = 100
    for i in range(num_bands):
        y0 = int(i * height / num_bands)
        y1 = int((i + 1) * height / num_bands)
        
        # Calculate interpolated color
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * i / num_bands)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * i / num_bands)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * i / num_bands)
        
        # Draw rectangle for this band
        draw.rectangle([(0, y0), (width, y1)], fill=(r, g, b))
    
    return bg

def create_team_matchup_image(match_id, team1_players, team2_players):
    """
    Create a stylized image showing the team matchups
    
    Args:
        match_id: The match ID
        team1_players: List of player dictionaries for team 1 with assigned_role
        team2_players: List of player dictionaries for team 2 with assigned_role
        
    Returns:
        str: Path to the created image
    """
    # Check for fonts, but don't raise an exception if we can't find them
    have_custom_fonts = download_fonts()
    
    # Image dimensions - make image larger to accommodate bigger fonts
    width = 3840  # 4K width (2x previous)
    height = 2160  # 4K height (2x previous)
    
    # Create the base image with a gradient background
    img = create_gradient_background(width, height, BACKGROUND_TOP, BACKGROUND_BOTTOM)
    draw = ImageDraw.Draw(img)
    
    # Add subtle design elements - decorative lines
    for i in range(10):
        # Draw diagonal lines in background
        start_x = int(width * i / 10)
        draw.line([(start_x, 0), (0, start_x)], fill=(*DARK_GRAY, 40), width=2)  # Top left diagonal lines
        draw.line([(width - start_x, 0), (width, start_x)], fill=(*DARK_GRAY, 40), width=2)  # Top right diagonal lines
    
    # Create header bar - increased height
    header_height = 240  # 2x previous
    header_overlay = Image.new('RGBA', (width, header_height), (*BLACK, 180))
    img.paste(header_overlay, (0, 0), header_overlay)
    
    # Create footer bar - increased height
    footer_height = 160  # 2x previous
    footer_overlay = Image.new('RGBA', (width, footer_height), (*BLACK, 180))
    img.paste(footer_overlay, (0, height - footer_height), footer_overlay)
    
    # Create center VS panel - increased size
    vs_panel_width = 600  # 2x previous
    vs_panel_height = 600  # 2x previous
    vs_panel = Image.new('RGBA', (vs_panel_width, vs_panel_height), (*BLACK, 120))
    img.paste(vs_panel, (width//2 - vs_panel_width//2, height//2 - vs_panel_height//2), vs_panel)
    
    # Draw border around VS panel
    panel_border_color = (*GOLD, 150)
    panel_x0 = width//2 - vs_panel_width//2
    panel_y0 = height//2 - vs_panel_height//2
    panel_x1 = width//2 + vs_panel_width//2
    panel_y1 = height//2 + vs_panel_height//2
    
    # Draw fancy border - increased width
    border_width = 6  # 2x previous
    for i in range(border_width):
        draw.rectangle([(panel_x0 - i, panel_y0 - i), (panel_x1 + i, panel_y1 + i)], 
                      outline=panel_border_color, width=2)  # Increased line width
    
    # Load and resize logo - increased size
    if LOGO_PATH.exists():
        try:
            logo = Image.open(LOGO_PATH)
            logo_width = width // 4  # Larger relative logo size
            logo_height = int(logo.height * (logo_width / logo.width))
            # Check if LANCZOS is available (Pillow versions may differ)
            resize_method = Image.LANCZOS if hasattr(Image, 'LANCZOS') else Image.ANTIALIAS
            logo = logo.resize((logo_width, logo_height), resize_method)
            
            # Paste logo in center
            logo_x = (width - logo_width) // 2
            logo_y = 10  # Position at top with slight offset
            # Check if logo has alpha channel
            if 'A' in logo.getbands():
                img.paste(logo, (logo_x, logo_y), logo)
            else:
                try:
                    img.paste(logo, (logo_x, logo_y), logo.convert('RGBA'))
                except Exception:
                    # If convert fails, just paste without transparency
                    img.paste(logo, (logo_x, logo_y))
        except Exception as e:
            print(f"Error loading logo: {e}")
    
    # Load fonts - first try truetype fonts if available, otherwise use default
    try:
        # Use system fonts or custom fonts if available
        if have_custom_fonts and (isinstance(DEFAULT_BOLD_FONT, str) and isinstance(DEFAULT_REGULAR_FONT, str) and 
            os.path.exists(DEFAULT_BOLD_FONT) and os.path.exists(DEFAULT_REGULAR_FONT)):
            # All font sizes increased by 4x
            title_font = ImageFont.truetype(str(DEFAULT_BOLD_FONT), 288)      # Was 72
            header_font = ImageFont.truetype(str(DEFAULT_BOLD_FONT), 192)     # Was 48
            player_name_font = ImageFont.truetype(str(DEFAULT_BOLD_FONT), 152) # Was 38
            detail_font = ImageFont.truetype(str(DEFAULT_REGULAR_FONT), 128)   # Was 32
            role_font = ImageFont.truetype(str(DEFAULT_BOLD_FONT), 128)        # Was 32
            footer_font = ImageFont.truetype(str(DEFAULT_REGULAR_FONT), 96)    # Was 24
        else:
            # Fallback to default PIL font - can't resize these much, so just using as-is
            title_font = ImageFont.load_default()
            header_font = ImageFont.load_default()
            player_name_font = ImageFont.load_default()
            detail_font = ImageFont.load_default()
            role_font = ImageFont.load_default()
            footer_font = ImageFont.load_default()
    except Exception as e:
        # If there's any error, use default fonts
        print(f"Error loading custom fonts: {e}")
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        player_name_font = ImageFont.load_default()
        detail_font = ImageFont.load_default()
        role_font = ImageFont.load_default()
        footer_font = ImageFont.load_default()
    
    # Draw title - adjusted position for larger text
    match_id_clean = match_id.replace('match_', '')
    title = f"MATCH #{match_id_clean}"
    # Draw text shadow
    draw.text((width // 2 + 4, 284), title, fill=BLACK, font=title_font, anchor="mm")
    # Draw actual text
    draw.text((width // 2, 280), title, fill=GOLD, font=title_font, anchor="mm")
    
    # Draw team headers with fancy styling - adjusted positions
    team1_x = width // 4
    team2_x = width - (width // 4)
    
    # Team 1 Header
    team1_text = "TEAM BLUE"
    # Text shadow
    draw.text((team1_x + 4, 404), team1_text, fill=BLACK, font=header_font, anchor="mm")
    # Main text
    draw.text((team1_x, 400), team1_text, fill=TEAM1_COLOR, font=header_font, anchor="mm")
    
    # Team 2 Header
    team2_text = "TEAM RED"
    # Text shadow
    draw.text((team2_x + 4, 404), team2_text, fill=BLACK, font=header_font, anchor="mm")
    # Main text
    draw.text((team2_x, 400), team2_text, fill=TEAM2_COLOR, font=header_font, anchor="mm")
    
    # Draw VS in the middle with styling - with larger glow
    vs_text = "VS"
    # Draw glowing effect - larger offsets for the glow
    for offset in range(2, 9, 2):  # Larger steps and range for more dramatic glow
        alpha = 100 - offset * 15
        if alpha > 0:
            draw.text((width // 2 + offset, height // 2 + offset), vs_text, 
                      fill=(*GOLD, alpha), font=title_font, anchor="mm")
    # Main VS text
    draw.text((width // 2, height // 2), vs_text, fill=GOLD, font=title_font, anchor="mm")
    
    # Get standard roles to ensure order
    standard_roles = ["top", "jungle", "mid", "bottom", "support"]
    
    # Group players by role
    team1_by_role = {}
    for player in team1_players:
        role = player.get('assigned_role', 'tbd').lower()
        team1_by_role[role] = player
    
    team2_by_role = {}
    for player in team2_players:
        role = player.get('assigned_role', 'tbd').lower()
        team2_by_role[role] = player
    
    # Draw player matchups by role with enhanced styling - adjusted for 4K resolution
    for i, role in enumerate(standard_roles):
        y_position = 540 + (i * 280)  # Doubled spacing
        
        # Create a semi-transparent row background for alternating rows
        if i % 2 == 0:
            row_overlay = Image.new('RGBA', (width, 160), (*BLACK, 40))  # Doubled height
            img.paste(row_overlay, (0, y_position - 80), row_overlay)
        
        # Draw connecting line for this matchup
        draw.line([(team1_x + 340, y_position), (team2_x - 340, y_position)], 
                  fill=GRAY, width=2)  # Doubled distance from center, increased width
        
        # Draw role indicator
        role_color = ROLE_COLORS.get(role, GRAY)
        # Draw role badge - circle with icon - larger circle
        circle_radius = 60  # Doubled radius
        circle_x = width // 2
        circle_y = y_position
        
        # Draw circle background
        draw.ellipse([(circle_x - circle_radius, circle_y - circle_radius), 
                      (circle_x + circle_radius, circle_y + circle_radius)], 
                    fill=role_color, outline=WHITE, width=4)  # Increased border width
        
        # Draw role text
        role_display = role[0].upper()  # Just first letter
        draw.text((circle_x, circle_y), role_display, 
                  fill=WHITE, font=role_font, anchor="mm")
        
        # Draw small role name below icon
        role_name = role.upper()
        draw.text((circle_x, circle_y + circle_radius + 30), role_name,  # Doubled offset
                  fill=LIGHT_GRAY, font=footer_font, anchor="mm")
        
        # Draw team 1 player with enhanced styling
        team1_player = team1_by_role.get(role)
        if team1_player:
            player_name = team1_player.get('game_name', 'Unknown')
            tier = team1_player.get('tier', 'unknown').capitalize()
            rank = team1_player.get('rank', '')
            
            # Draw player "card" background - larger card
            card_width = 600  # Doubled width
            card_height = 160  # Doubled height
            card_x = team1_x - (card_width // 2)
            card_y = y_position - (card_height // 2)
            player_card = Image.new('RGBA', (card_width, card_height), (*TEAM1_COLOR, 40))
            img.paste(player_card, (card_x, card_y), player_card)
            
            # Draw card border - thicker border
            for b in range(4):  # Doubled border width
                draw.rectangle([(card_x + b, card_y + b), 
                               (card_x + card_width - b, card_y + card_height - b)], 
                              outline=(*TEAM1_COLOR, 100), width=1)
            
            # Text shadow - larger offset
            draw.text((team1_x + 2, y_position - 30 + 2), player_name,  # Doubled offset
                      fill=BLACK, font=player_name_font, anchor="mm")
            # Player name with team color
            draw.text((team1_x, y_position - 30), player_name,  # Doubled offset
                      fill=TEAM1_COLOR, font=player_name_font, anchor="mm")
            
            # Player rank with white
            draw.text((team1_x, y_position + 40), f"{tier} {rank}",  # Doubled offset
                      fill=WHITE, font=detail_font, anchor="mm")
        
        # Draw team 2 player with enhanced styling
        team2_player = team2_by_role.get(role)
        if team2_player:
            player_name = team2_player.get('game_name', 'Unknown')
            tier = team2_player.get('tier', 'unknown').capitalize()
            rank = team2_player.get('rank', '')
            
            # Draw player "card" background - larger card
            card_width = 600  # Doubled width
            card_height = 160  # Doubled height
            card_x = team2_x - (card_width // 2)
            card_y = y_position - (card_height // 2)
            player_card = Image.new('RGBA', (card_width, card_height), (*TEAM2_COLOR, 40))
            img.paste(player_card, (card_x, card_y), player_card)
            
            # Draw card border - thicker border
            for b in range(4):  # Doubled border width
                draw.rectangle([(card_x + b, card_y + b), 
                               (card_x + card_width - b, card_y + card_height - b)], 
                              outline=(*TEAM2_COLOR, 100), width=1)
            
            # Text shadow - larger offset
            draw.text((team2_x + 2, y_position - 30 + 2), player_name,  # Doubled offset
                      fill=BLACK, font=player_name_font, anchor="mm")
            # Player name with team color
            draw.text((team2_x, y_position - 30), player_name,  # Doubled offset
                      fill=TEAM2_COLOR, font=player_name_font, anchor="mm")
            
            # Player rank with white
            draw.text((team2_x, y_position + 40), f"{tier} {rank}",  # Doubled offset
                      fill=WHITE, font=detail_font, anchor="mm")
    
    # Draw tournament credit in footer - adjusted position
    footer_text = "KSU ESPORTS TOURNAMENT"
    draw.text((width // 2, height - 60), footer_text,  # Doubled offset
              fill=GOLD, font=footer_font, anchor="mm")
    
    # Add timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d")
    draw.text((width - 40, height - 40), timestamp,  # Doubled offset
              fill=GRAY, font=footer_font, anchor="rb")
    
    # Add optional watermark
    watermark_text = "Generated by KSU Esports Bot"
    draw.text((40, height - 40), watermark_text,  # Doubled offset
              fill=GRAY, font=footer_font, anchor="lb")
    
    # Save the image with better quality
    try:
        # Try to use the defined output directory
        img_path = OUTPUT_DIR / f"match_{match_id}_teams.png"
        img.save(img_path, quality=95, optimize=True)  # Higher quality, optimized file
    except (PermissionError, OSError) as e:
        # If saving fails due to permission error, try using the system temp directory
        print(f"Warning: Could not save to {img_path}: {e}")
        import tempfile
        tmp_dir = pathlib.Path(tempfile.gettempdir())
        img_path = tmp_dir / f"match_{match_id}_teams.png"
        img.save(img_path, quality=95, optimize=True)
        
    return str(img_path)


def create_role_matchup_image(match_id, team1_players, team2_players):
    """
    Create a more detailed role matchup image
    
    Args:
        match_id: The match ID
        team1_players: List of player dictionaries for team 1 with assigned_role
        team2_players: List of player dictionaries for team 2 with assigned_role
        
    Returns:
        str: Path to the created image
    """
    # For now, this is just a placeholder that calls the standard image generation
    # In the future, this could be enhanced to show more detailed role-specific comparisons
    try:
        return create_team_matchup_image(match_id, team1_players, team2_players)
    except Exception as e:
        # Log error but don't crash
        print(f"Error in create_role_matchup_image: {e}")
        # Return None or use a fallback image
        return None