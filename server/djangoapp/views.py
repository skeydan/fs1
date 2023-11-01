from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
# from .models import related models
from .models import CarModel, CarMake, CarDealer
# from .restapis import related methods
from .restapis import get_dealers_from_cf, get_dealer_reviews_from_cf, get_dealer_by_id_from_cf
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.


# Create an `about` view to render a static about page
# def about(request):
def about(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/about.html', context)


# Create a `contact` view to return a static contact page
#def contact(request):
def contact(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/contact.html', context)


# Create a `login_request` view to handle sign in request
# def login_request(request):
def login_request(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Login successfully!")
            return redirect('djangoapp:index')
        else:
            messages.warning(request, "Invalid username or password.")
            return redirect("djangoapp:index")

# Create a `logout_request` view to handle sign out request
# def logout_request(request):
def logout_request(request):
    print("Log out the user `{}`".format(request.user.username))
    logout(request)
    return redirect('djangoapp:index.html')

# Create a `registration_request` view to handle sign up request
# def registration_request(request):
def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            pass
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            user.is_superuser = True
            user.is_staff=True
            user.save()  
            login(request, user)
            return redirect("djangoapp:index")
        else:
            return redirect("djangoapp:registration")


# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request):
    if request.method == "GET":
        context = {} #Create an empty dictionary named context
        url = "https://zkajdan-3000.theiadocker-0-labs-prod-theiak8s-4-tor01.proxy.cognitiveclass.ai/dealerships/get/"
        # Get dealers from the URL
        dealerships = get_dealers_from_cf(url)
        context['dealerships'] = dealerships #Assign the list of dealerships to the dealerships key in the context dictionary.
        # Concat all dealer's short name
        dealer_names = ' '.join([dealer.short_name for dealer in dealerships])
        # Return a list of dealer short name
        return render(request, 'djangoapp/index.html', context) #Return the rendered HTML template.

# Create a `get_dealer_details` view to render the reviews of a dealer
def get_dealer_details(request, id):
    if request.method == "GET":
        review_url = "https://zkajdan-5000.theiadocker-0-labs-prod-theiak8s-4-tor01.proxy.cognitiveclass.ai/api/get_reviews"
        reviews = get_dealer_reviews_from_cf(review_url, id=id)
        print(reviews)
        reviews_json = json.dumps(reviews)        
        # Create an HttpResponse with the JSON content
        response = HttpResponse(reviews_json, content_type='application/json')        
        return response


# Create a `add_review` view to submit a review
def add_review(request, id):
    context = {}
    url = "https://zkajdan-5000.theiadocker-0-labs-prod-theiak8s-4-tor01.proxy.cognitiveclass.ai/dealerships/get"
    dealer = get_dealer_by_id_from_cf(url, id=id)
    context["dealer"] = dealer
    if request.method == 'GET':
        # Get cars for the dealer
        cars = CarModel.objects.all()
        print(cars)
        context["cars"] = cars
        
        return render(request, 'djangoapp/add_review.html', context)
    elif request.method == 'POST':
        if request.user.is_authenticated:
            username = request.user.username
            print(request.POST)
            payload = dict()
            car_id = request.POST["car"]
            car = CarModel.objects.get(pk=car_id)
            payload["time"] = datetime.utcnow().isoformat()
            payload["name"] = username
            payload["dealership"] = id
            payload["id"] = id
            payload["review"] = request.POST["content"]
            payload["purchase"] = False
            if "purchasecheck" in request.POST:
                if request.POST["purchasecheck"] == 'on':
                    payload["purchase"] = True
            payload["purchase_date"] = request.POST["purchasedate"]
            payload["car_make"] = car.carmake.name
            payload["car_model"] = car.name
            payload["car_year"] = int(car.year.strftime("%Y"))

            new_payload = {}
            new_payload["review"] = payload
            review_post_url = "https://zkajdan-5000.theiadocker-0-labs-prod-theiak8s-4-tor01.proxy.cognitiveclass.ai/api/post_review"

            review = {
                "id":id,
                "time":datetime.utcnow().isoformat(),
                "name":request.user.username,  # Assuming you want to use the authenticated user's name
                "dealership" :id,                
                "review": request.POST["content"],  # Extract the review from the POST request
                "purchase": True,  # Extract purchase info from POST
                "purchase_date":request.POST["purchasedate"],  # Extract purchase date from POST
                "car_make": car.carmake.name,  # Extract car make from POST
                "car_model": car.name,  # Extract car model from POST
                "car_year": int(car.year.strftime("%Y")),  # Extract car year from POST
            }
            review=json.dumps(review,default=str)
            new_payload1 = {}
            new_payload1["review"] = review
            print("\nREVIEW:",review)
            post_request(review_post_url, review, id = id)
        return redirect("djangoapp:dealer_details", id = id)

