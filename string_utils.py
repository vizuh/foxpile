

def combine_and_split(args):
    combined_string = ' '.join(args)
    separated_args = combined_string.split(',')
    separated_args = filter(None, [arg.strip(', ') for arg in separated_args])
    return list(separated_args)


 
