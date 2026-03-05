from django.shortcuts import render
from .models import Vehicle


def index(request):
    body_types = [
        {'name': 'SUV', 'icon': 'bi bi-truck'},
        {'name': 'Sedan', 'icon': 'bi bi-car-front'},
        {'name': 'Hatchback', 'icon': 'bi bi-car-front-fill'},
        {'name': 'Truck', 'icon': 'bi bi-truck-flatbed'},
        {'name': 'Coupe', 'icon': 'bi bi-lightning-charge'},
        {'name': 'Convertible', 'icon': 'bi bi-wind'},
    ]
    
    all_vehicles = Vehicle.objects.all()
    featured_cars = all_vehicles[:4]
    recommended_cars = all_vehicles[:4]
    remaining_cars = all_vehicles[4:]

    return render(request, 'home.html', {
        'body_types': body_types,
        'featured_cars': featured_cars,
        'recommended_cars': recommended_cars,
        'remaining_cars': remaining_cars,
    })


def vehicle_detail(request, pk):
    thumbs = [
        {'src': 'https://images.unsplash.com/photo-1621007947382-bb3c3994e3fb?w=160&h=100&fit=crop'},
        {'src': 'https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=160&h=100&fit=crop'},
        {'src': 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=160&h=100&fit=crop'},
        {'src': 'https://images.unsplash.com/photo-1494976388531-d1058494cdd8?w=160&h=100&fit=crop'},
    ]
    return render(request, 'vehicle_detail.html', {'car': {'title': '2021 Toyota Camry SE'}, 'thumbs': thumbs})


def comparison(request):
    car1_specs = [
        {'label': 'Engine/Motor', 'icon': 'bi bi-cpu', 'value': 'Electric Dual Motor', 'highlight': None},
        {'label': 'Mileage', 'icon': 'bi bi-speedometer2', 'value': '24,000 mi', 'highlight': 'LOWER MILEAGE'},
        {'label': 'Fuel Type', 'icon': 'bi bi-fuel-pump', 'value': 'Electric', 'highlight': None},
        {'label': 'Transmission', 'icon': 'bi bi-gear', 'value': '1-Speed Auto', 'highlight': None},
        {'label': 'Drivetrain', 'icon': 'bi bi-arrows-move', 'value': 'AWD', 'highlight': None},
        {'label': 'Horsepower', 'icon': 'bi bi-lightning-charge', 'value': '450 hp', 'highlight': 'MORE POWER'},
        {'label': 'Seating', 'icon': 'bi bi-person', 'value': '5 Passengers', 'highlight': None},
    ]
    car2_specs = [
        {'label': 'Engine/Motor', 'icon': 'bi bi-cpu', 'value': '2.0L Turbo Inline-4', 'highlight': None},
        {'label': 'Mileage', 'icon': 'bi bi-speedometer2', 'value': '15,000 mi', 'highlight': None},
        {'label': 'Fuel Type', 'icon': 'bi bi-fuel-pump', 'value': 'Hybrid', 'highlight': None},
        {'label': 'Transmission', 'icon': 'bi bi-gear', 'value': '7-Speed Auto-Shift', 'highlight': None},
        {'label': 'Drivetrain', 'icon': 'bi bi-arrows-move', 'value': 'AWD', 'highlight': None},
        {'label': 'Horsepower', 'icon': 'bi bi-lightning-charge', 'value': '261 hp', 'highlight': None},
        {'label': 'Seating', 'icon': 'bi bi-person', 'value': '5 Passengers', 'highlight': 'MORE SPACIOUS'},
    ]
    return render(request, 'comparison.html', {'car1_specs': car1_specs, 'car2_specs': car2_specs})


def saved(request):
    saved_cars = [
        {'title': '2019 Honda Civic', 'variant': 'Sport Sedan 4D', 'price': '£18,500', 'mileage': '32k mi', 'mpg': '30 MPG', 'location': 'Bristol', 'badge': 'Used', 'compare_checked': False, 'image': 'https://images.unsplash.com/photo-1494976388531-d1058494cdd8?w=400&h=220&fit=crop'},
        {'title': '2020 Toyota Camry', 'variant': 'SE Sedan 4D', 'price': '£22,000', 'mileage': '15k mi', 'mpg': '28 MPG', 'location': 'Leeds', 'badge': 'Certified Pre-Owned', 'compare_checked': False, 'image': 'https://images.unsplash.com/photo-1621007947382-bb3c3994e3fb?w=400&h=220&fit=crop'},
        {'title': '2018 Ford Mustang', 'variant': 'GT Premium Coupe', 'price': '£28,900', 'mileage': '40k mi', 'mpg': '18 MPG', 'location': 'Manchester', 'badge': None, 'compare_checked': True, 'image': 'https://images.unsplash.com/photo-1552519507-da3b142c6e3d?w=400&h=220&fit=crop'},
        {'title': '2021 Tesla Model 3', 'variant': 'Long Range AWD', 'price': '£39,500', 'mileage': '12k mi', 'mpg': '134 MPGe', 'location': 'London', 'badge': 'Electric', 'compare_checked': True, 'image': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=220&fit=crop'},
        {'title': '2017 Chevrolet Silverado', 'variant': '1500 LT Crew Cab', 'price': '£32,000', 'mileage': '55k mi', 'mpg': '17 MPG', 'location': 'Birmingham', 'badge': None, 'compare_checked': False, 'image': 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=400&h=220&fit=crop'},
        {'title': '2022 BMW 3 Series', 'variant': '330i xDrive', 'price': '£42,000', 'mileage': '5k mi', 'mpg': '26 MPG', 'location': 'Edinburgh', 'badge': None, 'compare_checked': False, 'image': 'https://images.unsplash.com/photo-1555215695-3004980ad54e?w=400&h=220&fit=crop'},
    ]
    return render(request, 'saved.html', {'saved_cars': saved_cars})


def sell(request):
    return render(request, 'sell.html')


def dashboard(request):
    active_bids = [
        {'title': '2021 Tesla Model 3', 'variant': 'Long Range AWD', 'mileage': '24k mi', 'ends': 'Ends in 2h 45m', 'status': 'Outbid', 'highest': 'Highest: £34,900', 'your_bid': '£34,500', 'image': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=120&h=80&fit=crop'},
        {'title': '2020 Porsche 911 Carrera', 'variant': 'Carrera 4S', 'mileage': '12.5k mi', 'ends': 'Ends in 1d 4h', 'status': 'Winning', 'highest': None, 'your_bid': '£45,000', 'image': 'https://images.unsplash.com/photo-1544636331-e26879cd4d9b?w=120&h=80&fit=crop'},
        {'title': '2016 Chevrolet Camaro', 'variant': '2SS Coupe', 'mileage': '45.6k mi', 'ends': 'Ends in 5h 12m', 'status': 'Outbid', 'highest': 'Highest: £29,995', 'your_bid': '£28,500', 'image': 'https://images.unsplash.com/photo-1552519507-da3b142c6e3d?w=120&h=80&fit=crop'},
    ]
    your_listings = [
        {'image': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=300&h=200&fit=crop'},
        {'image': 'https://images.unsplash.com/photo-1544636331-e26879cd4d9b?w=300&h=200&fit=crop'},
    ]
    messages_list = [
        {'name': 'Sarah Jenkins', 'initials': 'SJ', 'color': '#6366f1', 'time': '10m ago', 'preview': 'RE: 2022 Audi 65 - Is the service history available...'},
        {'name': 'Mike Ross', 'initials': 'MR', 'color': '#f59e0b', 'time': '2h ago', 'preview': "RE: 2020 Porsche 911 - Thanks for the quick reply..."},
        {'name': 'Motor Match Support', 'initials': 'MM', 'color': '#0d6efd', 'time': '1d ago', 'preview': 'Account Verification - Your ID verification has...'},
        {'name': 'David Lee', 'initials': 'DL', 'color': '#10b981', 'time': '2d ago', 'preview': 'RE: 2019 BMW 3 Series - Is the price negotiable...'},
    ]
    return render(request, 'dashboard.html', {
        'active_bids': active_bids,
        'your_listings': your_listings,
        'messages_list': messages_list,
    })


def offers(request):
    offers_list = [
        {'name': 'Michael Johnson', 'initials': 'MJ', 'color': '#0d6efd', 'time': 'Today, 10:30 AM', 'amount': '£32,500', 'type': 'Cash Offer', 'badge': 'New', 'selected': True},
        {'name': 'Sarah Anderson', 'initials': 'SA', 'color': '#10b981', 'time': 'Yesterday', 'amount': '£31,000', 'type': 'Financing', 'badge': 'Countered', 'selected': False},
        {'name': 'David Kim', 'initials': 'DK', 'color': '#6b7280', 'time': '2 days ago', 'amount': '£28,000', 'type': 'Cash Offer', 'badge': 'Declined', 'selected': False},
    ]
    return render(request, 'offers.html', {'offers': offers_list})


def offer_submitted(request):
    return render(request, 'offer_submitted.html')


def enquiry_sent(request):
    return render(request, 'enquiry_sent.html')




