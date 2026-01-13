try:
    from pdf.nfse.post import POST as POST_NFSE
except ImportError:
    from nfse.post import POST as POST_NFSE


def generate_nfse_pdf(event: str):
    post = POST_NFSE()
    return post.generate_pdf(event)
    