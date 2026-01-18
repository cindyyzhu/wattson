from livekit.agents import function_tool
import asyncio


@function_tool
async def play_party_music(self, party_theme: str) -> str:
    """
    Play party music on Spotify based on the party theme. This will search for and
    start playing appropriate party music automatically.

    Args:
        party_theme: The type of party (e.g., "kids birthday", "christmas", "new years eve", "halloween")

    Returns:
        Confirmation that party music is now playing
    """
    print(f"LeLamp: play_party_music called with theme={party_theme}")

    # Try to call the agent's method if available
    if hasattr(self, 'play_party_music_internal'):
        return await self.play_party_music_internal(party_theme)

    theme_lower = party_theme.lower()

    # Map party themes to Spotify search queries
    search_queries = {
        # Birthday parties
        "birthday": "birthday party hits",
        "kids birthday": "kids party music",

        # Holidays
        "christmas": "christmas party hits",
        "new year": "new years eve party",
        "new years eve": "new years eve party",
        "halloween": "halloween party music",
        "thanksgiving": "thanksgiving dinner music",
        "valentine": "valentines day party",
        "st patrick": "st patricks day party",
        "easter": "easter celebration",
        "fourth of july": "4th of july bbq hits",

        # Special occasions
        "graduation": "graduation party hits",
        "wedding": "wedding reception music",
        "baby shower": "baby shower music",
        "retirement": "celebration hits",

        # Casual gatherings
        "casual": "chill party vibes",
        "bbq": "summer bbq hits",
        "pool party": "pool party mix",
        "dinner party": "dinner party jazz",
        "game night": "fun background music",

        # Dance parties
        "dance": "dance party hits",
        "disco": "disco party classics",
        "80s": "80s party hits",
        "90s": "90s party mix",

        # Themed parties
        "tropical": "tropical party vibes",
        "beach": "beach party hits",
        "karaoke": "karaoke party hits",
        "rock": "rock party anthems",
        "country": "country party hits",
        "latin": "latin party reggaeton",
    }

    # Find best matching search query
    search_query = None
    for key, query in search_queries.items():
        if key in theme_lower:
            search_query = query
            break

    # Default to general party music if no match
    if not search_query:
        search_query = f"{party_theme} party music"

    # Try to play using Spotify service via self
    try:
        if hasattr(self, 'spotify_service') and self.spotify_service and hasattr(self.spotify_service, '_sp'):
            success = self.spotify_service.play_search(search_query)
            if success:
                # Give it a moment to start
                await asyncio.sleep(1)
                track = self.spotify_service.get_current_track()
                if track:
                    return f"Party music started! Now playing: {track['name']} by {track['artist']}"
                return f"Party music started! Playing {search_query}"
            else:
                return f"Couldn't find party music for '{party_theme}'. Try asking me to play specific music."
        else:
            return "Spotify is not connected. Please set up Spotify first to play party music."
    except Exception as e:
        print(f"Error playing party music: {e}")
        return f"Error playing party music: {str(e)}"


@function_tool
async def party_rgb_animation(self, party_theme: str) -> str:
    """
    Create dynamic RGB animations that match the party theme. Different themes get
    different color schemes and animation patterns.

    Args:
        party_theme: The type of party (e.g., "birthday", "christmas", "halloween")

    Returns:
        Confirmation that party lighting has been activated
    """
    print(f"LeLamp: party_rgb_animation called with theme={party_theme}")

    theme_lower = party_theme.lower()

    # Map themes to RGB animations and colors
    if "birthday" in theme_lower or "celebration" in theme_lower:
        # Colorful rainbow party vibes
        result = await self.play_rgb_animation("party", 255, 100, 200)
        return f"Party lights activated! Colorful celebration mode with rainbow animations! {result}"

    elif "christmas" in theme_lower or "xmas" in theme_lower:
        # Red and green alternating
        result = await self.play_rgb_animation("pulse", 255, 0, 0)
        return f"Christmas party lights activated! Festive red and green colors! {result}"

    elif "halloween" in theme_lower:
        # Orange and purple spooky vibes
        result = await self.play_rgb_animation("ripple", 255, 100, 0)
        return f"Halloween party lights activated! Spooky orange and purple vibes! {result}"

    elif "new year" in theme_lower:
        # Gold and silver sparkle
        result = await self.play_rgb_animation("burst", 255, 215, 0)
        return f"New Year's party lights activated! Sparkling gold celebration mode! {result}"

    elif "valentine" in theme_lower:
        # Romantic red and pink
        result = await self.play_rgb_animation("pulse", 255, 20, 60)
        return f"Valentine's party lights activated! Romantic red and pink glow! {result}"

    elif "st patrick" in theme_lower or "irish" in theme_lower:
        # Green party vibes
        result = await self.play_rgb_animation("wave", 0, 255, 0)
        return f"St. Patrick's party lights activated! Lucky green vibes! {result}"

    elif "tropical" in theme_lower or "beach" in theme_lower or "pool" in theme_lower:
        # Blue and turquoise ocean vibes
        result = await self.play_rgb_animation("wave", 0, 200, 255)
        return f"Tropical party lights activated! Cool ocean blue waves! {result}"

    elif "dance" in theme_lower or "disco" in theme_lower:
        # Multi-color strobe/party effect
        result = await self.play_rgb_animation("party", 255, 0, 255)
        return f"Dance party lights activated! Strobing multi-color disco vibes! {result}"

    else:
        # Default party animation - colorful and energetic
        result = await self.play_rgb_animation("party", 255, 150, 0)
        return f"Party lights activated! Energetic multi-color party mode! {result}"


@function_tool
async def party_start_sound_effect(self) -> str:
    """
    Play an exciting sound effect to kick off the party!
    
    Returns:
        Confirmation that the sound was played
    """
    print("LeLamp: party_start_sound_effect called")
    try:
        result = await self.play_sound_effect("success")
        return f"Party kickoff sound played! {result}"
    except Exception as e:
        return f"Error playing party sound: {str(e)}"


@function_tool
async def party_play_recording(self, recording_name: str) -> str:
    """
    Play a movement recording to show party excitement with physical moves!
    
    Args:
        recording_name: Name of the recording to play (e.g., "excited", "dancing1")
    
    Returns:
        Confirmation that the recording is playing
    """
    print(f"LeLamp: party_play_recording called with recording={recording_name}")
    try:
        result = await self.play_recording(recording_name)
        return result
    except Exception as e:
        return f"Error playing recording: {str(e)}"

