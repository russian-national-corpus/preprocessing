from modules import common


def transform_token(in_token):
    transformation_sequence = []
    index_accumulator = 0
    for index, symbol in enumerate(in_token):
        transformed_symbol = transform_symbol(symbol)
        transformation_sequence.append((index, index_accumulator, symbol, transformed_symbol))
        if transformed_symbol:
            index_accumulator += 1
    return ''.join([operation[3] for operation in transformation_sequence]), transformation_sequence


def transform_symbol(in_symbol):
    if in_symbol in common.EDITOR_BRACKETS or in_symbol in common.ACCENTS:
        return ''
    elif in_symbol == common.PRETTY_APOSTROPHE:
        return common.APOSTROPHE
    else:
        return in_symbol.lower()


def detransform_token(in_transformation_sequence, in_index_range):
    begin, end = in_index_range
    detransformed_symbols = [(symbol, index)
                             for index, transformed_index, symbol, transformed_symbol
                             in in_transformation_sequence
                             if begin <= transformed_index < end]
    detransformed_token = ''.join([symbol for (symbol, index) in detransformed_symbols])
    return (detransformed_symbols[0][1], detransformed_symbols[-1][1] + 1), detransformed_token


def test():
    token = u'er[ge\u0300thewp[ro\u0301g]kj'
    transformed_token, transformation_sequence = transform_token(token)
    detransformed_token = detransform_token(transformation_sequence, (10, 20))
    print token.encode('utf-8')
    print transformed_token.encode('utf-8')
    print detransformed_token.encode('utf-8')


if __name__ == '__main__':
    test()
