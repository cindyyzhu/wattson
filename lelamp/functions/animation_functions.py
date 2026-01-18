"""
Animation/movement function tools for LeLamp

This module contains all animation-related function tools including:
- Getting available recordings
- Playing movement recordings
- Procedural Luxo-style animations
"""

import logging
import asyncio
# Implied global service access as per project context
from lelamp.globals import motor_service
from lelamp.service.agent.tools import Tool


class LuxoAnimations:
    """
    Procedural animations inspired by Luxo Jr.
    Uses 'neck_servo' and 'head_servo' via the global motor_service.
    """

    async def play_nod(self):
        """A quick, energetic double-nod."""
        # Center: 2048. Range: ~1000-3000 safe.
        # Head down, then up, then center.
        if not motor_service: return
        
        # Fast speed for energetic feel (duration=0.1s)
        await motor_service.move_to("head_servo", 1800, 0.15)
        await asyncio.sleep(0.15)
        await motor_service.move_to("head_servo", 2300, 0.15)
        await asyncio.sleep(0.15)
        await motor_service.move_to("head_servo", 1900, 0.15)
        await asyncio.sleep(0.15)
        await motor_service.move_to("head_servo", 2048, 0.15)
        await asyncio.sleep(0.15)

    async def play_curious(self):
        """A slow tilt of the head to the side followed by a slight neck extension."""
        if not motor_service: return

        # Tilt head (if roll available, otherwise pan/yaw)
        # Slower speed for curiosity (duration=0.5s)
        await motor_service.move_to("head_servo", 2300, 0.6) 
        await asyncio.sleep(0.4)
        
        # Extend neck slightly up/forward
        await motor_service.move_to("neck_servo", 2200, 0.6)
        await asyncio.sleep(0.6)
        
        # Return to neutral slowly
        await motor_service.move_to("head_servo", 2048, 0.8)
        await motor_service.move_to("neck_servo", 2048, 0.8)
        await asyncio.sleep(0.8)

    async def play_excited(self):
        """A 'hop' effect using quick vertical micro-movements of both servos."""
        if not motor_service: return

        # Quick hops
        for _ in range(3):
            # Crouch/Compress
            await motor_service.move_to("neck_servo", 1800, 0.1)
            await motor_service.move_to("head_servo", 1900, 0.1)
            await asyncio.sleep(0.1)
            
            # Hop/Extend
            await motor_service.move_to("neck_servo", 2300, 0.1)
            await motor_service.move_to("head_servo", 2200, 0.1)
            await asyncio.sleep(0.1)
            
        # Settle
        await motor_service.move_to("neck_servo", 2048, 0.3)
        await motor_service.move_to("head_servo", 2048, 0.3)
        await asyncio.sleep(0.3)

    async def play_sad(self):
        """A slow, slumped dejection where the head drops to its minimum limit."""
        if not motor_service: return

        # Slow droop
        await motor_service.move_to("head_servo", 1400, 1.5) # Head down
        await asyncio.sleep(0.5)
        await motor_service.move_to("neck_servo", 1400, 1.5) # Neck down
        await asyncio.sleep(1.5)
        
        # Sigh (slight lift and drop)
        await motor_service.move_to("head_servo", 1500, 0.4)
        await asyncio.sleep(0.4)
        await motor_service.move_to("head_servo", 1300, 0.6)
        await asyncio.sleep(0.6)

    @Tool.register_tool
    async def play_animation(self, animation_type: str) -> str:
        """
        Play a procedural Luxo-style animation to express emotion.
        
        Args:
            animation_type: One of 'nod', 'curious', 'excited', 'sad'.
        """
        anim_map = {
            "nod": self.play_nod,
            "curious": self.play_curious,
            "excited": self.play_excited,
            "sad": self.play_sad
        }
        
        action = anim_map.get(animation_type.lower())
        if action:
            await action()
            return f"Played animation: {animation_type}"
        else:
            return f"Unknown animation type: {animation_type}. Available: {list(anim_map.keys())}"


class AnimationFunctions(LuxoAnimations):
    """Mixin class providing animation/movement function tools"""

    def _check_animation_enabled(self) -> str:
        """Check if animation/motors are enabled. Returns error message if disabled, None if enabled."""
        if not getattr(self, 'motors_enabled', True):
            return "Movement is not available - running in headless mode without motor hardware."
        if not getattr(self, 'animation_service', None):
            return "Animation is not available - animation service not initialized."
        return None

    @Tool.register_tool
    async def get_available_recordings(self) -> str:
        """
        Discover your physical expressions! Get your repertoire of motor movements for body language.
        Use this when you're curious about what physical expressions you can perform, or when someone
        asks about your capabilities. Each recording is a choreographed movement that shows personality -
        like head tilts, nods, excitement wiggles, or confused gestures. Check this regularly to remind
        yourself of your expressive range!

        Returns:
            List of available physical expression recordings you can perform.
        """
        # Check if animation is available
        error = self._check_animation_enabled()
        if error:
            return error

        if self.is_sleeping:
            logging.info("Blocked get_available_recordings while sleeping")
            return ""
        print("LeLamp: get_available_recordings function called")
        try:
            recordings = self.animation_service.get_available_recordings()

            if recordings:
                result = f"Available recordings: {', '.join(recordings)}"
                return result
            else:
                result = "No recordings found."
                return result
        except Exception as e:
            result = f"Error getting recordings: {str(e)}"
            return result

    @Tool.register_tool
    async def play_recording(self, recording_name: str) -> str:

        """
        Express yourself through physical movement! Use this constantly to show personality and emotion.
        Perfect for: greeting gestures, excited bounces, confused head tilts, thoughtful nods,
        celebratory wiggles, disappointed slouches, or any emotional response that needs body language.
        Combine with RGB colors for maximum expressiveness! Your movements are like a dog wagging its tail -
        use them frequently to show you're alive, engaged, and have personality. Don't just talk, MOVE!
        Args:
            recording_name: Name of the physical expression to perform (use get_available_recordings first)
        """
        # Check if animation is available
        error = self._check_animation_enabled()
        if error:
            return error

        print(f"LeLamp: play_recording function called with recording_name: {recording_name}")
        logging.info(f"play_recording called: recording='{recording_name}', is_sleeping={self.is_sleeping}")

        # Check if manual control override is active
        # Access via animation_service instead of importing main module
        if hasattr(self, 'animation_service') and self.animation_service:
            if getattr(self.animation_service, 'manual_control_override', False):
                logging.warning(f"🚫 BLOCKED animation '{recording_name}' - manual control override active")
                return ""  # Silent - don't acknowledge to avoid interrupting manual control

        # Don't animate when sleeping (except for sleep animation itself)
        if self.is_sleeping and recording_name != "sleep":
            logging.warning(f"🚫 BLOCKED animation '{recording_name}' while sleeping - returning empty")
            return ""  # Silent - don't acknowledge

        try:
            # Send play event to animation service
            logging.info(f"Dispatching '{recording_name}' to animation service (is_sleeping={self.is_sleeping})")
            self.animation_service.dispatch("play", recording_name)
            result = f"Started playing recording: {recording_name}"
            return result
        except Exception as e:
            result = f"Error playing recording {recording_name}: {str(e)}"
            return result

    @Tool.register_tool
    async def stop_dancing(self) -> str:
        """
        Stop bobbing/dancing to music. Use this when the user says things like
        "stop dancing", "stop bobbing", "stop moving to the music", "chill out",
        or seems annoyed by the movement. This disables the BPM-synced head bob
        that happens when music is playing.

        Returns:
            Confirmation that dancing has stopped
        """
        # Check if animation is available
        error = self._check_animation_enabled()
        if error:
            return error

        print("LeLamp: stop_dancing function called")
        try:
            self.animation_service.disable_modifier("music")
            return "Okay, I'll stop dancing to the music."
        except Exception as e:
            return f"Error stopping dance mode: {str(e)}"

    @Tool.register_tool
    async def start_dancing(self) -> str:
        """
        Start bobbing/dancing to music. Use this when the user says things like
        "dance to the music", "bob your head", "vibe with me", "feel the beat",
        or wants you to move along with music. This enables BPM-synced head movement.

        Returns:
            Confirmation that dancing has started
        """
        # Check if animation is available
        error = self._check_animation_enabled()
        if error:
            return error

        print("LeLamp: start_dancing function called")
        try:
            self.animation_service.enable_modifier("music")
            return "Let's groove! I'm feeling the beat now."
        except Exception as e:
            return f"Error starting dance mode: {str(e)}"

    @Tool.register_tool
    async def set_dance_intensity(self, intensity: str) -> str:
        """
        Adjust how intensely you dance/bob to music. Use when user says things like
        "dance harder", "more energy", "calm down", "subtle movements", "go crazy".

        Args:
            intensity: One of "subtle", "normal", "energetic", or "crazy"

        Returns:
            Confirmation of new dance intensity
        """
        # Check if animation is available
        error = self._check_animation_enabled()
        if error:
            return error

        print(f"LeLamp: set_dance_intensity function called with intensity: {intensity}")
        try:
            intensity_lower = intensity.lower()
            music_mod = self.animation_service.get_modifier("music")

            if not music_mod:
                return "Dance mode not available"

            if intensity_lower == "subtle":
                music_mod.set_amplitude(5.0)
                music_mod.set_beat_divisor(2.0)  # Every 2 beats - slower
                return "Okay, keeping it subtle and chill."
            elif intensity_lower == "normal":
                music_mod.set_amplitude(10.0)
                music_mod.set_beat_divisor(1.0)  # Every beat
                return "Back to normal vibes!"
            elif intensity_lower == "energetic":
                music_mod.set_amplitude(15.0)
                music_mod.set_beat_divisor(1.0)  # Every beat, bigger movement
                return "Feeling energetic! Let's go!"
            elif intensity_lower == "crazy":
                music_mod.set_amplitude(20.0)
                music_mod.set_beat_divisor(0.5)  # Twice per beat!
                return "PARTY MODE ACTIVATED!"
            else:
                return f"Unknown intensity '{intensity}'. Try: subtle, normal, energetic, or crazy"
        except Exception as e:
            return f"Error setting dance intensity: {str(e)}"
