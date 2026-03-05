from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def offers(request):
    offers_list = [
        {'name': 'Michael Johnson', 'amount': '£32,500', 'type': 'Cash Offer'},
        {'name': 'Sarah Anderson',  'amount': '£31,000', 'type': 'Financing'},
        {'name': 'David Kim',       'amount': '£28,000', 'type': 'Cash Offer'},
    ]
    return render(request, 'offers/offers.html', {'offers': offers_list})


def offer_submitted(request):
    return render(request, 'offers/offer_submitted.html')
