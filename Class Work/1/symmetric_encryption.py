class OTP:
    def __init__(self, seed):
        """
        :param seed: the seed
        :type seed: int
        """
        self.seed = seed
        self.otp = seed

    def __next__(self):
        self.seed = self.otp ** 2




def main():
    print((5**2).to_bytes(1, "big"))


if __name__ == '__main__':
    main()
