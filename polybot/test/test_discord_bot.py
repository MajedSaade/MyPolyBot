import unittest
from polybot.bot import ImageProcessingBot
from polybot.img_proc import Img

class TestDiscordBot(unittest.TestCase):

    def setUp(self):
        self.bot = ImageProcessingBot()

    def test_bot_initialization(self):
        """Test if bot initializes properly"""
        self.assertIsNotNone(self.bot)

    def test_img_contour(self):
        """Test if image contour runs without error"""
        img = Img("polybot/test/beatles.jpeg")
        result = img.contour()
        self.assertIsNotNone(result)

    def test_img_rotate(self):
        """Test rotate functionality"""
        img = Img("polybot/test/beatles.jpeg")
        result = img.rotate()
        self.assertIsNotNone(result)

if __name__ == '__main__':
    unittest.main()
