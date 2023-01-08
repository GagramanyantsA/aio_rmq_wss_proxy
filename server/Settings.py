class Settings:
    LJUST_SYMBOLS = 15

    @staticmethod
    def format_name(name: str):
        return name.ljust(Settings.LJUST_SYMBOLS)
