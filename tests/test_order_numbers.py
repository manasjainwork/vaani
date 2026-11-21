import pytest

from vaani.order_numbers import parse_order_number


@pytest.mark.parametrize(
    "heard",
    [
        "2057",
        "mera order number 2057 hai",
        "order number do zero paanch saat tha",
        "मेरा ऑर्डर नंबर दो शून्य पाँच सात है",
        "ऑर्डर नंबर २०५७ है",
        "two zero five seven",
        "20 57",
        "ऑर्डर नंबर दो ज़ीरो पाँच सात",
    ],
)
def test_finds_the_number(heard):
    assert parse_order_number(heard) == "2057"


@pytest.mark.parametrize(
    "heard",
    [
        "अडर नमवर दो जीरो पाज साथ फाज",  # garbled by speech recognition
        "mera order kab aayega",
        "",
        "20570",  # five digits
        "205",  # three digits
        "order 2057 aur 3141",  # two numbers, not sure which one
        "kar do 2057",  # "do" can mean "give", so this is not safe to read
    ],
)
def test_refuses_to_guess(heard):
    assert parse_order_number(heard) is None
