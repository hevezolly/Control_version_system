import chardet


def _get_starting_chunk(filename, length=1024):
    """
    :param filename: File to open and get the first little chunk of.
    :param length: Number of bytes to read, default 1024.
    :returns: Starting chunk of bytes.
    """
    if filename is None:
        return b''
    with open(filename, 'rb') as f:
        chunk = f.read(length)
        return chunk


_control_chars = b'\n\r\t\f\b'
_printable_ascii = _control_chars + bytes(range(32, 127))
_printable_high_ascii = bytes(range(127, 256))


def _is_binary(bytes_to_check):
    """
    Uses a simplified version of the Perl detection algorithm,
    based roughly on Eli Bendersky's translation to Python:
    http://eli.thegreenplace.net/2011/10/19/perls-guess-if-file-is-text-or-binary-implemented-in-python/
    This is biased slightly more in favour of deeming files as text
    files than the Perl algorithm, since all ASCII compatible character
    sets are accepted as text, not just utf-8.
    :param bytes_to_check: A chunk of bytes to check.
    :returns: True if appears to be a binary, otherwise False.
    """

    if not bytes_to_check:
        return False

    low_chars = bytes_to_check.translate(None, _printable_ascii)
    nontext_ratio1 = len(low_chars) / len(bytes_to_check)

    high_chars = bytes_to_check.translate(None, _printable_high_ascii)
    nontext_ratio2 = len(high_chars) / len(bytes_to_check)

    if nontext_ratio1 > 0.90 and nontext_ratio2 > 0.90:
        return True

    is_likely_binary = (
        (nontext_ratio1 > 0.3 and nontext_ratio2 < 0.05) or
        (nontext_ratio1 > 0.8 and nontext_ratio2 > 0.8)
    )

    detected_encoding = chardet.detect(bytes_to_check)

    decodable_as_unicode = False
    if (detected_encoding['confidence'] > 0.9 and
            detected_encoding['encoding'] != 'ascii'):
        bytes_to_check.decode(encoding=detected_encoding['encoding'])
        decodable_as_unicode = True

    if is_likely_binary:
        return not decodable_as_unicode
    else:
        if decodable_as_unicode:
            return False
        else:
            return (b'\x00' in bytes_to_check
                    or b'\xff' in bytes_to_check)


def is_binary_file(filename, length=1024):
    chank = _get_starting_chunk(filename, length)
    return _is_binary(chank)
