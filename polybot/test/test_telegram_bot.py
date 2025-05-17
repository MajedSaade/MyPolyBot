import unittest
from polybot.bot import ImageProcessingBot
from polybot.img_proc import Img


class TestDiscordBot(unittest.TestCase):
    def setUp(self):
        self.bot = ImageProcessingBot(token="FAKE_TOKEN")

    def test_bot_initialization(self):
        self.assertIsNotNone(self.bot)

    def test_img_rotate(self):
        # Optional: test bot has rotate command or functionality
        self.assertTrue(hasattr(self.bot, "process_image"))

    def test_img_contour(self):
        self.assertTrue(hasattr(self.bot, "process_image"))

if __name__ == "__main__":
    unittest.main()

