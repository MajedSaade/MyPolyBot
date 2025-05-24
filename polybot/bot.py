import discord
from discord.ext import commands
from discord.ext.commands import Bot
from loguru import logger
import os
import time
import random
import re
import requests
from pathlib import Path
from polybot.img_proc import Img
import json
import asyncio
import subprocess
import shutil
import webbrowser


class Bot:
    def __init__(self, token):
        # Set up intents for Discord bot
        intents = discord.Intents.default()
        intents.message_content = True
        # Create a Discord bot client
        self.client = commands.Bot(command_prefix='!', intents=intents)
        self.token = token

        # Set up event handlers
        @self.client.event
        async def on_ready():
            logger.info(f'Discord Bot logged in as {self.client.user}')

        @self.client.event
        async def on_message(message):
            # Avoid responding to own messages
            if message.author == self.client.user:
                return
            # Process commands
            await self.client.process_commands(message)
            # Default message handler
            if not message.content.startswith('!'):
                await self.handle_message(message)

    async def start(self):
        """Start the Discord bot"""
        await self.client.start(self.token)

    async def send_text(self, channel_id, text):
        """Send a text message to a channel"""
        channel = self.client.get_channel(channel_id)
        if channel:
            await channel.send(text)

    async def send_text_with_quote(self, channel_id, text, quoted_msg_id):
        """Send a text message with a quote reference"""
        channel = self.client.get_channel(channel_id)
        if channel:
            # In Discord, we need to find the message first
            try:
                quoted_msg = await channel.fetch_message(quoted_msg_id)
                await quoted_msg.reply(text)
            except discord.NotFound:
                # Message not found, send without quote
                await channel.send(text)

    def is_current_msg_photo(self, message):
        """Check if message contains a photo"""
        return len(message.attachments) > 0 and message.attachments[0].content_type.startswith('image/')

    async def download_user_photo(self, message):
        """Download photo from a message"""
        if not self.is_current_msg_photo(message):
            raise RuntimeError(f'Message content of type photo expected')
        attachment = message.attachments[0]
        folder_name = 'photos'
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        file_path = f"{folder_name}/{attachment.filename}"
        await attachment.save(file_path)
        return file_path

    async def send_photo(self, channel_id, img_path):
        """Send a photo to a channel"""
        if not os.path.exists(img_path):
            raise RuntimeError("Image path doesn't exist")
        channel = self.client.get_channel(channel_id)
        if channel:
            await channel.send(file=discord.File(img_path))

    async def handle_message(self, message):
        """Bot Main message handler with expanded conversational abilities"""
        logger.info(f'Incoming message: {message.content}')
        # Convert message to lowercase for easier matching
        content = message.content.lower()
        username = message.author.name

        # GREETINGS
        greetings = ["hi", "hello", "hey", "hola", "greetings", "sup", "yo", "howdy",
                     "hi there", "hello there", "heya", "hiya", "good morning",
                     "good afternoon", "good evening", "what's up", "wassup"]
        if any(content == greeting for greeting in greetings):
            greeting_responses = [
                f"Hello {username}! How can I help you today? 👋",
                f"Hi there, {username}! Ready for some image processing? 📸",
                f"Hey {username}! Great to see you! What can I help with?",
                f"Greetings, {username}! How may I assist you today?",
                f"Hello! I'm here and ready to help with your images! 🖼️",
                f"Hey there! Ready when you are. What shall we create today?",
                f"Hi {username}! Looking forward to seeing what images we'll work with today!",
                f"Hello {username}! Got any cool images to transform today?",
                f"Hey! Welcome! I'm all set to help with your image editing needs.",
                f"Greetings! Hope you're having a fantastic day! Ready to work with some images?"
            ]
            await message.channel.send(random.choice(greeting_responses))
            return

        # HOW ARE YOU and FEELINGS
        how_are_you_patterns = [
            r"how are you", r"how('s| is) it going", r"how are you doing",
            r"how('s| is) your day", r"how do you (feel|do)", r"what's up",
            r"how('s| is) everything", r"how have you been", r"how do you feel"
        ]
        if any(re.search(pattern, content) for pattern in how_are_you_patterns):
            feeling_responses = [
                f"I'm doing great, {username}! Ready to process some images for you! 📸",
                f"I'm functioning perfectly! How can I help with your images today?",
                f"All systems operational! What images would you like to work with today?",
                f"I'm at your service and ready to help with image processing! How about you?",
                f"I'm having a wonderful day processing images! How are you?",
                f"I'm excellent! Always happy when I get to help with creative projects!",
                f"Never better! I love helping with image transformations. How are you doing?",
                f"I'm fantastic! Ready to apply some amazing effects to your images!",
                f"I'm doing well, thanks for asking! I'm excited to see what we'll create today!",
                f"I'm great! Each day brings new images and creative possibilities!"
            ]
            await message.channel.send(random.choice(feeling_responses))
            return

        # USER FEELING GOOD
        feeling_good_patterns = [
            r"(i('m| am)|feeling) (good|great|excellent|fantastic|amazing|wonderful|happy)",
            r"(i'm|i am) (doing|feeling) (good|great|fine)",
            r"(good|great|fine|okay|not bad|alright|excellent|amazing)"
        ]
        if any(re.search(pattern, content) for pattern in feeling_good_patterns):
            positive_responses = [
                f"That's great to hear, {username}! Ready to work on some images together?",
                f"Awesome! Glad you're doing well. What can I help you with today?",
                f"Excellent! That positive energy will make our image processing even better!",
                f"Wonderful! Let's channel that good mood into some creative image work!",
                f"Fantastic! Let's make your day even better with some cool image effects!",
                f"That's what I like to hear! Let's keep that positive vibe going with some fun image processing!",
                f"Brilliant! Your good mood is contagious! What shall we create today?",
                f"Happy to hear that! Good moods and creativity go hand in hand!"
            ]
            await message.channel.send(random.choice(positive_responses))
            return

        # USER FEELING BAD
        feeling_bad_patterns = [
            r"(i('m| am)|feeling) (bad|sad|depressed|unhappy|tired|exhausted|sick)",
            r"(not|n't) (good|great|fine|okay|feeling well)",
            r"(terrible|awful|horrible|lousy)"
        ]
        if any(re.search(pattern, content) for pattern in feeling_bad_patterns):
            sympathy_responses = [
                f"I'm sorry to hear that, {username}. Maybe working with some images might cheer you up?",
                f"I hope you feel better soon! Let me know if processing some photos might help distract you.",
                f"That's unfortunate. Would you like to create something cool to lift your spirits?",
                f"Sorry to hear that. Sometimes a bit of creativity can help - want to try some image effects?",
                f"I wish I could help you feel better. Would transforming some images be a good distraction?",
                f"That's tough. Creating something can sometimes help when you're feeling down. Want to try?",
                f"I'm sorry you're not feeling your best. Image processing can be therapeutic sometimes."
            ]
            await message.channel.send(random.choice(sympathy_responses))
            return

        # THANK YOU
        thanks_patterns = [
            r"thank you", r"thanks", r"thx", r"thank u", r"appreciate it",
            r"grateful", r"thanks a lot", r"thank you (so|very) much"
        ]
        if any(re.search(pattern, content) for pattern in thanks_patterns):
            gratitude_responses = [
                "You're welcome! 😊",
                f"Happy to help, {username}!",
                "Anytime! Need anything else?",
                "My pleasure! Let me know if you need any other image processing.",
                "Glad I could help! That's what I'm here for.",
                "No problem at all! Is there anything else you'd like to do with your images?",
                "You're very welcome! Feel free to call on me whenever you need image processing.",
                "It was my pleasure to assist you! Don't hesitate to ask if you need anything else.",
                "You got it! Always happy to help with your image processing needs!"
            ]
            await message.channel.send(random.choice(gratitude_responses))
            return

        # GOODBYE
        goodbye_patterns = [
            r"^bye$", r"goodbye", r"see you", r"cya", r"later", r"good night",
            r"good day", r"i('m| am) (leaving|going)", r"have to go", r"talk (to you )?later"
        ]
        if any(re.search(pattern, content) for pattern in goodbye_patterns):
            farewell_responses = [
                f"Goodbye, {username}! Come back when you have more images to process!",
                f"See you later, {username}! 👋",
                f"Until next time, {username}!",
                f"Bye {username}! Have a great day!",
                f"Take care, {username}! I'll be here when you need more image processing.",
                f"Farewell! Looking forward to our next creative session!",
                f"Goodbye! Don't forget to come back with more cool images to transform!",
                f"See you soon! Can't wait to see what images you bring next time!",
                f"Have a wonderful day! I'll be here ready to help when you return."
            ]
            await message.channel.send(random.choice(farewell_responses))
            return

        # JOKES
        joke_patterns = [
            r"tell (me )?(a )?joke", r"(got|know) (any )?jokes",
            r"(be|say something) funny", r"make me laugh", r"humor me"
        ]
        if any(re.search(pattern, content) for pattern in joke_patterns):
            jokes = [
                "Why don't scientists trust atoms? Because they make up everything!",
                "Why did the scarecrow win an award? Because he was outstanding in his field!",
                "I told my wife she was drawing her eyebrows too high. She looked surprised!",
                "Why don't photographers tell jokes? Because they take things too literally!",
                "Why couldn't the bicycle stand up by itself? It was two-tired!",
                "Why did the picture go to jail? It was framed!",
                "What's a robot's favorite type of image? A PNG file because it's 'pinging'!",
                "How many photographers does it take to change a light bulb? Just one, but they'll take 50 shots to get it right!",
                "What do you call a fake image? A photoshop!",
                "I tried to take a picture of fog the other day. I mist.",
                "What did the image say to the filter? 'You change me!'",
                "Why was the computer cold? It left its Windows open!",
                "How does a photographer greet people? They say 'Cheese!'",
                "What's black and white and read all over? A newspaper! ...Or an image in contour mode!"
            ]
            await message.channel.send(random.choice(jokes))
            return

        # COMPLIMENTS
        if re.search(
                r"(you('re| are)|your) (great|awesome|amazing|helpful|excellent|wonderful|fantastic|good|smart|clever)",
                content):
            compliment_responses = [
                "Thank you! I try my best to be helpful! 😊",
                "That's very kind of you to say!",
                "I appreciate the compliment! It's my pleasure to assist with your images.",
                "Thanks! I'm always trying to improve my image processing skills!",
                "You're too kind! I'm glad I can be of service.",
                "Thank you for the positive feedback! It means a lot!",
                "You just made my day! I love helping with image processing."
            ]
            await message.channel.send(random.choice(compliment_responses))
            return

        # TIME/DATE
        if re.search(r"what (time|day|date) is it", content) or re.search(r"what('s| is) the (time|date)", content):
            from datetime import datetime
            now = datetime.now()
            date_str = now.strftime("%A, %B %d, %Y")
            time_str = now.strftime("%I:%M %p")
            await message.channel.send(f"It's currently {time_str} on {date_str}.")
            return

        # WEATHER (simulate since we don't have an API)
        if re.search(r"(how('s| is) the )?weather", content):
            weather_responses = [
                "I don't have access to real-time weather data, but I hope it's nice where you are!",
                "I can't check the weather, but I hope you're having a beautiful day!",
                "While I can't tell you the actual weather, it's always sunny in image processing land!",
                "I don't have weather information, but whatever the weather, it's a good day for image editing!"
            ]
            await message.channel.send(random.choice(weather_responses))
            return

        # HELP COMMANDS
        if re.search(r"help|commands|what can you do|how (do|to) (use|work)|(show|list) commands", content):
            help_message = (
                "**📷 Image Processing Bot - Commands:**\n\n"
                "• `!blur [level]` - Blur an image\n"
                "• `!contour` - Detect edges in an image\n"
                "• `!rotate` - Rotate an image 90° clockwise\n"
                "• `!salt_pepper` - Add noise to an image\n"
                "• `!segment` - Convert image to black & white\n"
                "• `!detect` - Detect objects in an image using YOLO\n"
                "• `!concat [horizontal|vertical]` - Join two images\n"
                "• `!ask [question]` - Ask the AI a question using Ollama\n"
                "• `!songrec` - Get personalized song recommendations\n"
                "• `!spotify [song name/artist]` - Search for music on Spotify\n\n"
                "For image commands like `!blur`, attach an image to your message.\n"
                "For `!concat`, the bot will use the two most recent images in the channel.\n\n"
                "You can also just chat with me! I respond to greetings, questions about how I'm doing, jokes, and more!"
            )
            await message.channel.send(help_message)
            return

        # ABOUT/WHO ARE YOU
        if re.search(r"about|who are you|what are you|tell me about yourself", content):
            about_message = (
                "I'm an Image Processing Bot! 🤖\n\n"
                "I can help you apply various effects and transformations to your images. "
                "Upload an image with one of my commands, and I'll process it for you.\n\n"
                "I can detect objects in your images using the YOLO model!\n\n"
                "With my Ollama integration, I can answer questions using AI models!\n\n"
                "I can recommend songs based on your preferences, and even open Spotify to play them!\n\n"
                "I can also chat with you about your day, tell jokes, and "
                "try to be a helpful companion for all your needs!\n\n"
                "Type `help` or use the `!help` command to see what I can do!"
            )
            await message.channel.send(about_message)
            return

        # FAVORITE COLOR
        if re.search(r"(what('s| is)|tell me) your favorite color", content):
            color_responses = [
                "As an image processing bot, I love all colors! But if I had to choose, probably #00AAFF - a nice digital blue!",
                "I'm particularly fond of RGB(0, 170, 255) - it's a lovely shade of cyan!",
                "I appreciate all colors of the spectrum, but there's something special about that perfect shade of digital blue.",
                "All colors are beautiful in their own way! Though I do have a soft spot for vibrant blues and cyans."
            ]
            await message.channel.send(random.choice(color_responses))
            return

        # FAVORITE IMAGE/PHOTO
        if re.search(r"(what('s| is)|tell me) your favorite (image|photo|picture)", content):
            image_responses = [
                "My favorite images are the ones I get to help process! I love seeing creativity in action.",
                "I appreciate all sorts of images, but I have a special fondness for landscape photography with lots of detail to process.",
                "I don't play favorites, but I do enjoy images with interesting contrasts and patterns that really showcase what my filters can do!",
                "Every image has its own unique beauty. That said, I do love detailed images that transform dramatically when processed."
            ]
            await message.channel.send(random.choice(image_responses))
            return

        # DEFAULT RESPONSE
        default_responses = [
            f"I'm not sure how to respond to that. Would you like to try processing an image?",
            f"Interesting! If you'd like to process an image, just use one of my commands like !blur or !rotate.",
            f"I'm here primarily to help with image processing. Type 'help' to see what I can do!",
            f"Would you like to try one of my image processing commands? Type 'help' to see the options.",
            f"I'm not quite sure what you mean. I'd be happy to help process an image if you'd like!"
        ]
        await message.channel.send(random.choice(default_responses))


class QuoteBot(Bot):
    async def handle_message(self, message):
        """Quote bot message handler"""
        logger.info(f'Incoming message: {message.content}')
        if message.content != 'Please dont quote me':
            await message.reply(message.content)


class ImageProcessingBot(Bot):
    def __init__(self, token, yolo_url=None, ollama_url=None):
        super().__init__(token)
        # Define the YOLO service URL - can be overridden in environment variables
        self.yolo_url = yolo_url or os.environ.get('YOLO_URL', 'http://10.0.1.90:8081/predict')
        logger.info(f"YOLO service URL set to: {self.yolo_url}")

        # Define the Ollama service URL - can be overridden in environment variables
        self.ollama_url = ollama_url or os.environ.get('OLLAMA_URL', 'http://10.0.0.136:11434/api/chat')
        self.ollama_model = os.environ.get('OLLAMA_MODEL', 'gemma3:1b')
        logger.info(f"Ollama service URL set to: {self.ollama_url}")
        logger.info(f"Ollama model set to: {self.ollama_model}")

        # Store the current state of user conversations
        self.conversation_state = {}

        # Register commands
        @self.client.command(name='blur')
        async def blur(ctx, blur_level: int = 16):
            await self.process_image(ctx, 'blur', blur_level=blur_level)

        @self.client.command(name='contour')
        async def contour(ctx):
            await self.process_image(ctx, 'contour')

        @self.client.command(name='rotate')
        async def rotate(ctx):
            await self.process_image(ctx, 'rotate')

        @self.client.command(name='salt_pepper')
        async def salt_pepper(ctx):
            await self.process_image(ctx, 'salt_n_pepper')

        @self.client.command(name='segment')
        async def segment(ctx):
            await self.process_image(ctx, 'segment')

        @self.client.command(name='detect')
        async def detect(ctx):
            """Detect objects in an image using YOLO"""
            await self.detect_objects(ctx)

        @self.client.command(name='ask')
        async def ask(ctx, *, question: str):
            """Ask a question to Ollama"""
            await self.ask_ollama(ctx, question)

        @self.client.command(name='songrec')
        async def songrec(ctx):
            """Get song recommendations based on your preferences"""
            await self.song_recommendation_flow(ctx)

        @self.client.command(name='spotify')
        async def spotify(ctx, *, query: str = None):
            """Search for a song on Spotify or open the Spotify app"""
            if not query:
                await ctx.send("Please provide a search query. Usage: `!spotify <song name or artist>`")
                return
            
            await self.open_spotify_search(ctx, query)

        @self.client.command(name='concat')
        async def concat(ctx, direction: str = 'horizontal'):
            """
            Concatenate the last two images sent in the channel.
            Usage: !concat [horizontal|vertical]
            """
            if direction not in ['horizontal', 'vertical']:
                await ctx.send("Direction must be either 'horizontal' or 'vertical'")
                return

            # We need to find the two most recent image attachments
            channel = ctx.channel
            image_attachments = []
            # Get recent messages with attachments
            async for message in channel.history(limit=20):
                if message.attachments and message.attachments[0].content_type.startswith('image/'):
                    image_attachments.append(message.attachments[0])
                    if len(image_attachments) >= 2:
                        break

            if len(image_attachments) < 2:
                await ctx.send("Need at least two image attachments in recent messages to concatenate.")
                return

            try:
                # Download both images
                file_path1 = f"photos/concat_1.{image_attachments[0].filename.split('.')[-1]}"
                file_path2 = f"photos/concat_2.{image_attachments[1].filename.split('.')[-1]}"
                await image_attachments[0].save(file_path1)
                await image_attachments[1].save(file_path2)

                # Process images
                img1 = Img(file_path1)
                img2 = Img(file_path2)

                # Concatenate
                img1.concat(img2, direction=direction)

                # Save the processed image
                new_path = img1.save_img()

                # Send the processed image
                await ctx.send(f"Concatenated images {direction}ly:", file=discord.File(new_path))
            except Exception as e:
                logger.error(f"Error concatenating images: {e}")
                await ctx.send(f"Error concatenating images: {e}")

    async def process_image(self, ctx, operation, **kwargs):
        """Process an image attachment with the specified operation"""
        if not ctx.message.attachments:
            await ctx.send("Please attach an image to process.")
            return

        attachment = ctx.message.attachments[0]
        if not attachment.content_type.startswith('image/'):
            await ctx.send("The attachment must be an image.")
            return

        # Download the image
        try:
            file_path = await self.download_user_photo(ctx.message)

            # Process image
            img = Img(file_path)

            # Apply the requested operation
            if operation == 'blur':
                img.blur(blur_level=kwargs.get('blur_level', 16))
            elif operation == 'contour':
                img.contour()
            elif operation == 'rotate':
                img.rotate()
            elif operation == 'salt_n_pepper':
                img.salt_n_pepper()
            elif operation == 'segment':
                img.segment()

            # Save the processed image
            new_path = img.save_img()

            # Send the processed image
            await ctx.send(f"Processed image with {operation}:", file=discord.File(new_path))
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            await ctx.send(f"Error processing image: {e}")

    async def detect_objects(self, ctx):
        """Send image to YOLO service for object detection"""
        if not ctx.message.attachments:
            await ctx.send("Please attach an image to detect objects.")
            return

        attachment = ctx.message.attachments[0]
        if not attachment.content_type.startswith('image/'):
            await ctx.send("The attachment must be an image.")
            return

        # Download the image
        try:
            file_path = await self.download_user_photo(ctx.message)

            # Let the user know we're working on it
            processing_msg = await ctx.send("🔍 Detecting objects in your image... Please wait.")

            # Send the image to YOLO service
            with open(file_path, 'rb') as img_file:
                try:
                    # FIXED LINE: Removed the "/predict" from the URL since it's already in self.yolo_url
                    logger.info(f"[DEBUG] Sending request to: {self.yolo_url}")
                    response = requests.post(
                        self.yolo_url,
                        files={"file": img_file}
                    )

                    # Check if the request was successful
                    if response.status_code != 200:
                        await processing_msg.edit(
                            content=f"Error: YOLO service returned status code {response.status_code}")
                        return

                    # Parse the result
                    result = response.json()

                    # Extract detected objects
                    objects = result.get("labels", [])
                    count = result.get("detection_count", 0)

                    if count == 0:
                        await processing_msg.edit(content="No objects detected in the image.")
                    else:
                        # Count occurrences of each object
                        object_counts = {}
                        for obj in objects:
                            object_counts[obj] = object_counts.get(obj, 0) + 1

                        # Format the result message
                        if count == 1:
                            detection_msg = f"I detected 1 object in your image:"
                        else:
                            detection_msg = f"I detected {count} objects in your image:"

                        # Add detected objects with counts
                        for obj, cnt in object_counts.items():
                            if cnt == 1:
                                detection_msg += f"\n• {obj}"
                            else:
                                detection_msg += f"\n• {obj} ({cnt})"

                        await processing_msg.edit(content=detection_msg)
                except requests.RequestException as e:
                    logger.error(f"Error connecting to YOLO service: {e}")
                    await processing_msg.edit(
                        content=f"Error: Could not connect to the YOLO service. Please try again later.")
        except Exception as e:
            logger.error(f"Error during object detection: {e}")
            await ctx.send(f"Error during object detection: {e}")

    async def ask_ollama(self, ctx, question):
        """Send a question to Ollama and return the response"""
        # Let the user know we're working on it
        processing_msg = await ctx.send(f"🤔 Thinking about: '{question}' ... Please wait.")

        try:
            # Ensure model name includes the tag for specific model version (e.g., gemma3:1b)
            model_name = self.ollama_model
            
            # Prepare the data for the Ollama API - Using the proper format for Ollama API
            data = {
                "model": model_name,
                "messages": [{"role": "user", "content": question}],
                "stream": False
            }

            # The correct endpoint is /api/chat for chat-based interactions
            api_endpoint = self.ollama_url
            if not api_endpoint.endswith('/api/chat'):
                # If the URL doesn't end with /api/chat, ensure we're using the right endpoint
                api_endpoint = api_endpoint.rstrip('/') + '/api/chat'
            
            # Log the request details for debugging
            logger.info(f"[DEBUG] Sending request to Ollama: {api_endpoint}")
            logger.info(f"[DEBUG] Using model: {model_name}")
            logger.info(f"[DEBUG] Request data: {data}")
            
            # Send the request to the Ollama API
            response = requests.post(
                api_endpoint,
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=180  # Updated timeout to 3 minutes
            )

            # Check if the request was successful
            if response.status_code != 200:
                logger.error(f"[ERROR] Ollama returned status code {response.status_code}")
                logger.error(f"[ERROR] Response content: {response.text}")
                await processing_msg.edit(
                    content=f"Error: Ollama service returned status code {response.status_code}. Please check your server configuration.")
                return

            # Parse the result
            result = response.json()
            logger.info(f"[DEBUG] Response received: {result}")

            # Extract the response - updated for chat API response format
            ai_response = result.get("message", {}).get("content", "I'm sorry, I couldn't generate a response.")

            # Format and send the response
            formatted_response = f"**Question:** {question}\n\n**Answer:** {ai_response}"

            # Discord has a 2000 character limit
            if len(formatted_response) > 1990:
                formatted_response = formatted_response[:1990] + "..."
            await processing_msg.edit(content=formatted_response)
        except requests.RequestException as e:
            logger.error(f"Error connecting to Ollama service: {e}")
            await processing_msg.edit(
                content=f"Error: Could not connect to the Ollama service. Please check if Ollama is running at {self.ollama_url}.")
        except Exception as e:
            logger.error(f"Error during Ollama request: {e}")
            await ctx.send(f"Error during Ollama request: {e}")

    async def song_recommendation_flow(self, ctx):
        """Interactive flow to get song recommendations based on user preferences"""
        # Let the user know we're starting the recommendation flow
        await ctx.send("🎵 Welcome to Song Recommendations! I'll ask you a few questions to find the perfect songs for you.")
        
        # Get the user ID
        user_id = str(ctx.author.id)
        
        # Initialize the conversation state
        self.conversation_state[user_id] = {
            'flow': 'song_recommendation',
            'question_index': 0,
            'preferences': {}
        }
        
        # Ask the first question
        questions = [
            {"key": "language", "question": "What language would you prefer for the songs? (e.g., English, Spanish, Korean, etc.)"},
            {"key": "genre", "question": "What genre of music do you like? (e.g., Pop, Rock, Hip-hop, Jazz, Classical, etc.)"},
            {"key": "mood", "question": "What mood are you in? (e.g., Happy, Sad, Energetic, Relaxed, etc.)"},
            {"key": "era", "question": "From which time period would you prefer songs? (e.g., 60s, 80s, 90s, 2000s, 2010s, Recent, etc.)"},
            {"key": "artist_type", "question": "Do you prefer solo artists or bands? (or type 'any' if no preference)"}
        ]
        
        # Ask the first question to start the flow
        await ctx.send(questions[0]["question"])
    
    async def get_song_recommendations(self, channel, prompt, preferences):
        """Get song recommendations from Ollama based on user preferences"""
        # Let the user know we're working on it
        processing_msg = await channel.send("🎧 Finding the perfect songs for you... Please wait.")
        
        try:
            # Prepare the data for the Ollama API
            data = {
                "model": self.ollama_model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False
            }
            
            # The correct endpoint is /api/chat for chat-based interactions
            api_endpoint = self.ollama_url
            if not api_endpoint.endswith('/api/chat'):
                api_endpoint = api_endpoint.rstrip('/') + '/api/chat'
            
            # Send the request to the Ollama API
            response = requests.post(
                api_endpoint,
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=180  # Updated timeout to 3 minutes
            )
            
            # Check if the request was successful
            if response.status_code != 200:
                logger.error(f"[ERROR] Ollama returned status code {response.status_code}")
                logger.error(f"[ERROR] Response content: {response.text}")
                await processing_msg.edit(
                    content=f"Error: Couldn't get song recommendations. Please try again later.")
                return
                
            # Parse the result
            result = response.json()
            
            # Extract the response
            ai_response = result.get("message", {}).get("content", "I couldn't generate song recommendations.")
            
            # Process the AI response to format it better and fix links
            processed_response = self.process_song_recommendations(ai_response)
            
            # Format the response with a header
            formatted_response = f"**🎵 Song Recommendations Based On Your Preferences 🎵**\n\n"
            formatted_response += f"**Language:** {preferences['language']}\n"
            formatted_response += f"**Genre:** {preferences['genre']}\n"
            formatted_response += f"**Mood:** {preferences['mood']}\n"
            formatted_response += f"**Era:** {preferences['era']}\n"
            formatted_response += f"**Artist Type:** {preferences['artist_type']}\n\n"
            formatted_response += processed_response
            
            # Discord has a 2000 character limit
            if len(formatted_response) > 1990:
                # Split into multiple messages if too long
                parts = [formatted_response[i:i+1990] for i in range(0, len(formatted_response), 1990)]
                await processing_msg.edit(content=parts[0])
                for part in parts[1:]:
                    await channel.send(part)
            else:
                await processing_msg.edit(content=formatted_response)
                
        except requests.RequestException as e:
            logger.error(f"Error connecting to Ollama service: {e}")
            await processing_msg.edit(
                content=f"Error: Could not connect to the Ollama service. Please check if Ollama is running.")
        except Exception as e:
            logger.error(f"Error during song recommendation: {e}")
            await channel.send(f"Error during song recommendation: {e}")
    
    def process_song_recommendations(self, ai_response):
        """Process the AI response to format song recommendations better"""
        # Create a more structured format for the recommendations
        try:
            # First, try to extract song information using regex patterns
            import re
            
            # Clean up the response - remove any markdown formatting that might interfere
            cleaned_response = ai_response.replace("*", "").replace(",\n", "\n").replace(".,", ".")
            
            # Initialize the formatted output
            formatted_output = ""
            
            # Find all songs in the response
            songs = re.findall(r'(?:Song Title:|^\d+\.\s+)([^,\n]+).*?Artist Name:([^,\n]+).*?Year of Release:([^,\n]+).*?YouTube Link:.*?\[(.*?)\]\((.*?)\).*?Description:([^,\n]+)', 
                              cleaned_response, re.DOTALL | re.MULTILINE)
            
            # If no songs found with the pattern, try an alternative pattern
            if not songs:
                songs = re.findall(r'(?:Song Title:|^\d+\.\s+)([^,\n]+).*?Artist Name:([^,\n]+).*?Year of Release:([^,\n]+).*?YouTube Link:(?:\s+)?(https?://[^\s]+).*?Description:([^,\n]+)', 
                                  cleaned_response, re.DOTALL | re.MULTILINE)
            
            # If still no songs found, try another pattern that might match the format
            if not songs:
                songs = re.findall(r'(?:Song Title:|^\d+\.\s+)(.*?)(?:Artist Name:|👤\s+Artist:)(.*?)(?:Year of Release:|📅\s+Year:)(.*?)(?:YouTube Link:|🎵\s+Link:)(.*?)(?:Description:|💬)(.*?)(?:\n\n|$)', 
                                  cleaned_response, re.DOTALL | re.MULTILINE)
            
            # If still no songs found, return the original response
            if not songs:
                return ai_response
            
            # Format each song
            for i, song in enumerate(songs, 1):
                if len(song) >= 5:  # Make sure we have all the needed parts
                    title = song[0].strip()
                    artist = song[1].strip()
                    year = song[2].strip()
                    
                    # Handle different link formats
                    if len(song) == 6:  # First pattern with markdown link
                        link_text = song[3].strip()
                        link_url = song[4].strip()
                        description = song[5].strip()
                    else:  # Second pattern with direct URL
                        link_url = song[3].strip()
                        description = song[4].strip()
                        link_text = "YouTube"
                    
                    # Extract URL from text if needed
                    url_match = re.search(r'(https?://[^\s]+)', link_url)
                    if url_match:
                        link_url = url_match.group(1)
                    
                    # Clean up URL - remove trailing punctuation
                    link_url = link_url.rstrip('.,;:!?')
                    
                    # Ensure the URL is properly formatted
                    if not link_url.startswith(('http://', 'https://')):
                        link_url = f"https://{link_url}"
                    
                    # Create a search query for Spotify
                    spotify_query = f"{title} {artist}"
                    
                    # URL encode for web search
                    import urllib.parse
                    encoded_query = urllib.parse.quote(f"{title} {artist}")
                    spotify_web_url = f"https://open.spotify.com/search/{encoded_query}"
                    
                    # Format the song information
                    formatted_output += f"**{i}. {title}**\n"
                    formatted_output += f"👤 **Artist:** {artist}\n"
                    formatted_output += f"📅 **Year:** {year}\n"
                    # In Discord, plain URLs are automatically clickable
                    formatted_output += f"🎵 **YouTube:** {link_url}\n"
                    formatted_output += f"🎵 **Spotify:** [Open in Web]({spotify_web_url}) or use `!spotify {spotify_query}`\n"
                    formatted_output += f"💬 **Why you'll like it:** {description}\n\n"
            
            # If we successfully formatted at least one song, return the formatted output
            if formatted_output:
                # Add a note about links
                formatted_output += "**Note:** You can click the Spotify web links to open in your browser, or use the `!spotify` command to open in the desktop app (if installed). Enjoy your music! 🎧"
                return formatted_output
            
            # Fallback to original response if formatting failed
            return ai_response
            
        except Exception as e:
            logger.error(f"Error formatting song recommendations: {e}")
            # Return the original response if there was an error in formatting
            return ai_response

    async def open_spotify_search(self, ctx, query):
        """Open Spotify with the given search query or URL"""
        try:
            # Check if Spotify is installed
            spotify_installed = shutil.which("spotify") is not None
            
            # Check if the query is a Spotify URL or URI
            if query.startswith(("spotify:", "https://open.spotify.com/")):
                # It's a direct Spotify URL/URI
                if query.startswith("https://open.spotify.com/"):
                    # It's already a web URL, we can use it directly for web browser
                    web_url = query
                    
                    # Convert web URL to Spotify URI for desktop app
                    parts = query.split("/")
                    if len(parts) >= 5:
                        resource_type = parts[3]  # track, album, artist, playlist
                        resource_id = parts[4].split("?")[0]  # Remove query parameters
                        spotify_uri = f"spotify:{resource_type}:{resource_id}"
                else:
                    # It's a Spotify URI, need to convert to web URL for browser
                    # Format: spotify:track:1234567890
                    parts = query.split(":")
                    if len(parts) >= 3:
                        resource_type = parts[1]  # track, album, artist, playlist
                        resource_id = parts[2]
                        web_url = f"https://open.spotify.com/{resource_type}/{resource_id}"
                        spotify_uri = query
            else:
                # It's a search query
                # Encode the query for URL safety
                import urllib.parse
                encoded_query = urllib.parse.quote(query)
                
                # Create the Spotify search URL/URI
                spotify_uri = f"spotify:search:{encoded_query}"
                web_url = f"https://open.spotify.com/search/{encoded_query}"
            
            # Open Spotify based on availability
            if spotify_installed:
                # Let the user know we're opening the desktop app
                await ctx.send(f"🎵 Opening Spotify app to search for: **{query}**")
                # Use subprocess to open Spotify with the URI
                subprocess.Popen(["/snap/bin/spotify", spotify_uri], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                success_msg = "Spotify desktop app should now be open with your request!"
            else:
                # Let the user know we're opening the web version
                await ctx.send(f"🎵 Opening Spotify Web to search for: **{query}**")
                # Open the web browser with the Spotify web URL
                webbrowser.open(web_url)
                success_msg = "Spotify Web should now be open in your browser with your request!"
            
            # Send success message
            await ctx.send(success_msg)
            
        except Exception as e:
            logger.error(f"Error opening Spotify: {e}")
            await ctx.send(f"Error opening Spotify: {e}. Try opening https://open.spotify.com/ manually.")

    async def handle_message(self, message):
        """Enhanced message handler that can handle both image processing and song recommendations"""
        logger.info(f'Incoming message: {message.content}')
        user_id = str(message.author.id)
        
        # Check if the user is in an active song recommendation flow
        if user_id in self.conversation_state:
            current_state = self.conversation_state[user_id]
            
            # If they're in the song recommendation flow, process their response
            if current_state.get('flow') == 'song_recommendation':
                # Process their response according to the current question
                question_idx = current_state.get('question_index', 0)
                preferences = current_state.get('preferences', {})
                
                # Update preferences with user's response
                questions = [
                    {"key": "language", "question": "What language would you prefer for the songs?"},
                    {"key": "genre", "question": "What genre of music do you like?"},
                    {"key": "mood", "question": "What mood are you in?"},
                    {"key": "era", "question": "From which time period would you prefer songs?"},
                    {"key": "artist_type", "question": "Do you prefer solo artists or bands?"}
                ]
                
                if question_idx < len(questions):
                    # Store the user's answer to the current question
                    preferences[questions[question_idx]["key"]] = message.content
                    
                    # Move to the next question
                    question_idx += 1
                    self.conversation_state[user_id]['question_index'] = question_idx
                    self.conversation_state[user_id]['preferences'] = preferences
                    
                    # If there are more questions, ask the next one
                    if question_idx < len(questions):
                        await message.channel.send(questions[question_idx]["question"])
                        return
                    else:
                        # All questions answered, generate recommendations
                        await message.channel.send("Thanks for your preferences! Searching for song recommendations now... 🔍")
                        
                        # Create a prompt for Ollama
                        prompt = f"""Based on the following preferences, recommend the top 5 songs:
- Language: {preferences['language']}
- Genre: {preferences['genre']}
- Mood: {preferences['mood']}
- Era: {preferences['era']}
- Artist Type: {preferences['artist_type']}

For each song, provide:
1. Song title
2. Artist name
3. Year of release
4. A direct YouTube link to the song (must be a real, working YouTube link in the format https://www.youtube.com/watch?v=VIDEOID)
5. A brief one-sentence description of why this song matches the preferences

IMPORTANT:
- Format each song as a separate numbered item
- Make sure all YouTube links are direct, valid links that work when clicked
- Use the format https://www.youtube.com/watch?v=VIDEOID for all YouTube links
- Do not use shortened URLs or mobile (m.youtube.com) links
- Verify that each song actually exists and matches the preferences
- Do not include any markdown formatting in the links, just provide the plain URL
"""
                        # Clear the conversation state once we're done
                        del self.conversation_state[user_id]
                        
                        # Send the request to Ollama
                        await self.get_song_recommendations(message.channel, prompt, preferences)
                        return
                
                return  # End early if in song recommendation flow
        
        # If not in a special flow, handle as a normal message
        content = message.content.lower()
        username = message.author.name

        # Check for Spotify play commands (must check before super() call to avoid default responses)
        play_match = re.search(r"^play\s+(.+)$", content)
        if play_match:
            query = play_match.group(1).strip()
            if query:
                await message.channel.send(f"🎵 I'll open Spotify to play: **{query}**")
                await self.open_spotify_search(message.channel, query)
                return

        # Handle greetings and other typical messages using the parent class implementation
        await super().handle_message(message)
        
        # Check for keywords related to song recommendations
        song_keywords = ["song", "music", "recommend", "playlist", "track", "artist", "singer", "band", "album"]
        if any(keyword in content for keyword in song_keywords) and "songrec" not in content and not content.startswith("play"):
            await message.channel.send(f"Would you like me to recommend some songs based on your preferences, {username}? Try using the `!songrec` command!")
            return