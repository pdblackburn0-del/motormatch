import argparse
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from motormatch.models import Vehicle


def seed(force=False):
    if not force:
        print(
            "Aborted: pass --force to confirm deletion of all vehicles "
            "before seeding."
        )
        return
    Vehicle.objects.all().delete()
    
    cars_data = [
        {'title': '2021 Tesla Model 3', 'price': '£34,900', 'variant': 'Long Range AWD', 'mileage': '24k mi', 'year': '2021', 'fuel': 'Electric', 'transmission': 'Auto', 'badge': 'HOT DEAL', 'badge_color': '#16a34a', 'image': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=220&fit=crop'},
        {'title': '2019 BMW 3 Series', 'price': '£28,500', 'variant': '330i xDrive', 'mileage': '42k mi', 'year': '2019', 'fuel': 'Gas', 'transmission': 'Auto', 'badge': 'PRICE DROP', 'badge_color': '#dc2626', 'image': 'https://images.unsplash.com/photo-1555215695-3004980ad54e?w=400&h=220&fit=crop'},
        {'title': '2022 Audi Q5', 'price': '£41,200', 'variant': '45 TFSI Premium', 'mileage': '15k mi', 'year': '2022', 'fuel': 'Hybrid', 'transmission': 'Auto', 'badge': 'ECO', 'badge_color': '#16a34a', 'image': 'https://images.unsplash.com/photo-1606152421802-db97b9c7a11b?w=400&h=220&fit=crop'},
        {'title': '2020 Honda Accord', 'price': '£22,900', 'variant': 'Touring Sedan', 'mileage': '31k mi', 'year': '2020', 'fuel': 'Gas', 'transmission': 'Auto', 'badge': 'HOT DEAL', 'badge_color': '#16a34a', 'image': 'https://images.unsplash.com/photo-1494976388531-d1058494cdd8?w=400&h=220&fit=crop'},
        {'title': '2020 Porsche 911', 'variant': 'Carrera 4S', 'price': '£45,000', 'mileage': '12.5k mi', 'year': '2020', 'fuel': 'Petrol', 'transmission': 'Auto', 'image': 'https://images.unsplash.com/photo-1544636331-e26879cd4d9b?w=400&h=220&fit=crop'},
        {'title': '2023 BMW X5', 'variant': 'xDrive40i', 'price': '£62,950', 'mileage': '5.2k mi', 'year': '2023', 'fuel': 'Hybrid', 'image': 'https://images.unsplash.com/photo-1555215695-3004980ad54e?w=400&h=220&fit=crop'},
        {'title': '2018 Toyota Camry', 'variant': 'SE Sedan', 'price': '£18,500', 'mileage': '54k mi', 'year': '2018', 'fuel': 'Gas', 'image': 'https://images.unsplash.com/photo-1621007947382-bb3c3994e3fb?w=400&h=220&fit=crop'},
        {'title': '2021 Ford F-150', 'variant': 'XLT SuperCrew', 'price': '£38,900', 'mileage': '32.1k mi', 'year': '2021', 'fuel': 'Gas', 'image': 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=400&h=220&fit=crop'},
        {'title': '2022 Mercedes-Benz C-Class', 'variant': 'C 300 4MATIC', 'price': '£55,400', 'mileage': '8.9k mi', 'year': '2022', 'fuel': 'Gas', 'image': 'https://images.unsplash.com/photo-1549399542-7e3f8b79c341?w=400&h=220&fit=crop'},
        {'title': '2016 Chevrolet Camaro', 'variant': '2SS Coupe', 'price': '£29,995', 'mileage': '45.6k mi', 'year': '2016', 'fuel': 'Gas', 'image': 'https://images.unsplash.com/photo-1552519507-da3b142c6e3d?w=400&h=220&fit=crop'},
        {'title': '2019 Honda Civic', 'variant': 'Sport Sedan 4D', 'price': '£18,500', 'mileage': '32k mi', 'year': '2019', 'fuel': 'Gas', 'badge': 'Used', 'image': 'https://images.unsplash.com/photo-1494976388531-d1058494cdd8?w=400&h=220&fit=crop'},
        {'title': '2020 Toyota Camry', 'variant': 'SE Sedan 4D', 'price': '£22,000', 'mileage': '15k mi', 'year': '2020', 'fuel': 'Gas', 'badge': 'Certified Pre-Owned', 'image': 'https://images.unsplash.com/photo-1621007947382-bb3c3994e3fb?w=400&h=220&fit=crop'},
        {'title': '2018 Ford Mustang', 'variant': 'GT Premium Coupe', 'price': '£28,900', 'mileage': '40k mi', 'year': '2018', 'fuel': 'Gas', 'image': 'https://images.unsplash.com/photo-1552519507-da3b142c6e3d?w=400&h=220&fit=crop'},
        {'title': '2017 Chevrolet Silverado', 'variant': '1500 LT Crew Cab', 'price': '£32,000', 'mileage': '55k mi', 'year': '2017', 'fuel': 'Gas', 'image': 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=400&h=220&fit=crop'},
        {'title': '2022 BMW 3 Series', 'variant': '330i xDrive', 'price': '£42,000', 'mileage': '5k mi', 'year': '2022', 'fuel': 'Gas', 'image': 'https://images.unsplash.com/photo-1555215695-3004980ad54e?w=400&h=220&fit=crop'},
    ]
    
    for data in cars_data:
        Vehicle.objects.create(**data)

    print(f"Successfully seeded {len(cars_data)} vehicles.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Seed the vehicle database.')
    parser.add_argument(
        '--force',
        action='store_true',
        help='Required: confirms deletion of all existing vehicles.',
    )
    args = parser.parse_args()
    seed(force=args.force)
