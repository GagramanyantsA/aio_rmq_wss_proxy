class Utils:
    LJUST_SYMBOLS = 15

    @staticmethod
    def format_name(name: str):
        return name.ljust(Utils.LJUST_SYMBOLS)
