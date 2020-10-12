
import json
import dateutil.parser
import babel
import datetime
import sys
import calendar 

from pytz import utc
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import app, db, Venue, Artist, Show

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

moment = Moment(app)
app.config.from_object('config')
db.init_app(app)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

def format_time(time):
    date = str(time.strftime('%A')) + ', ' + str(time.strftime('%d')) + ' ' + str(time.strftime('%B')) + ' ' + str(time.year) + ' ' + str(time.strftime('%I')) + ':' + str(time.strftime('%M')) + ' ' + str(time.strftime('%p'))
    return date



#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():

  def getShows(venue_id):
    now = datetime.now(tz=None)
    return len(Show.query.filter(Show.venue_id==venue_id).filter(Show.start_time>now).all())
    # return len(number)

  def createVenueObj(id, name, num_upcoming_shows):
    return {
      "id": id,
      "name": name,
      "num_upcoming_shows": num_upcoming_shows
    }

  uniqueCity = set()
  total = Venue.query.all()
  data = []

  for venue in total: 
      num_upcoming_shows = getShows(venue.id)
      temp_venue = createVenueObj(venue.id, venue.name, num_upcoming_shows)

      if venue.city not in uniqueCity:
        temp = {
          "city": venue.city,
          "state": venue.state,
          "venues": [temp_venue]
        }
        data.append(temp)
        uniqueCity.add(venue.city)
      else: 
        for city in data: 
          if city['city'] == venue.city:
            city['venues'].append(temp_venue)
      
  return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST', 'GET'])
def search_venues():  

  search_term = request.form.get('search_term', '') 

  venues = Venue.query.filter(Venue.name.ilike("%" + search_term + "%")).all()
  response = {}
  data = []

  for venue in venues:
    temp_data = {}
    temp_data = {
      "id": venue.id,
      "name": venue.name
    }
    data.append(temp_data)

  response['count'] = len(venues)
  response['data'] = data

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  def createShowObj(artist_id, artist_name, artist_image_link, start_time):
    return {
      'artist_id': artist_id,
      'artist_name': artist_name, 
      'artist_image_link': artist_image_link,
      'start_time': start_time
    }
  error = False
  try:
    all_past_shows = db.session.query(Artist, Show).join(Show).join(Venue).\
      filter(
        Show.venue_id==venue_id,
        Show.artist_id==Artist.id,
        Show.start_time < datetime.now(tz=None)
      ).\
      all()
    
    all_upcoming_shows = db.session.query(Artist, Show).join(Show).join(Venue).\
      filter(
        Show.venue_id==venue_id,
        Show.artist_id==Artist.id,
        Show.start_time > datetime.now(tz=None)
      ).\
      all()

    upcoming_shows = []
    past_shows = []

    for artist, show in all_upcoming_shows:
      upcoming_shows.append(createShowObj(artist.id, artist.name, artist.image_link, show.start_time))

    for artist, show in all_past_shows:
      past_shows.append(createShowObj(artist.id, artist.name, artist.image_link, show.start_time))

    venue = Venue.query.get(venue_id)  

    data = {
      'id': venue.id, 
      'name': venue.name,
      'genres': venue.genres,
      'address': venue.address,
      'city': venue.city,
      'state': venue.state,
      'phone': venue.phone,
      'website': venue.website,
      'facebook_link': venue.facebook_link,
      'seeking_talent': venue.seeking_talent,
      'seeking_description': venue.seeking_description,
      'image_link': venue.image_link,
      'upcoming_shows': upcoming_shows,
      'past_shows': past_shows,
      'past_shows_count': len(past_shows),
      'upcoming_shows_count': len(upcoming_shows)
    }
  except: 
    error = True 
  if error: 
    abort(500)
  else:
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  form = VenueForm(request.form)
  props = {}
  try:
    for att in form: 
      if(att.name != 'csrf_token' and att.name != 'genres'):
        props[att.name] = att.data
    
    props['genres'] = form.genres.data
    venue = Venue(**props)
    db.session.add(venue)
    db.session.commit()
    venue_id = venue.id
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info)
  finally:
    db.session.close()
  if error: 
    flash('An error occured. Venue ' + request.form['name'] + ' failed to list.')
    return render_template('pages/home.html')
  else:
    return redirect(url_for('show_venue', venue_id=venue.id))
  


@app.route('/venues/<venue_id>', methods=['POST'])
def delete_venue(venue_id):
  
  error = False
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    flash('Venue ' + venue.name + ' successfully deleted.')
  except: 
    db.session.rollback()
    error = True
  finally:
    db.session.close()
  if error: 
    flash('An error occured. Venue ' + venue.name + ' could not be deleted.')
    return rredirect(url_for('index'))
  else:
    return redirect(url_for('index'))


  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  return render_template('pages/artists.html', artists=Artist.query.all())

@app.route('/artists/search', methods=['POST', 'GET'])
def search_artists():


  search_term = request.form.get('search_term', '') 

  artists = Artist.query.filter(Artist.name.ilike("%" + search_term + "%")).all()
  response = {}
  data = []

  for artist in artists: 
    temp_data = {}
    temp_data = {
      "id": artist.id,
      "name": artist.name
    }
    data.append(temp_data)
  
  response['count'] = len(artists)
  response['data'] = data 
 
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

  artist = Artist.query.get(artist_id)
  if artist is None:
    abort(404)

  shows = Show.query.filter_by(artist_id=artist_id).all()
  todayDate = datetime.utcnow()
  upcoming_shows = []
  past_shows = []

  for show in shows:
    temp_show = {}
    venue = Venue.query.get(show.venue_id)
    start_time = format_time(show.start_time)
    temp_show = {
      "start_time": start_time,
      "venue_id": show.venue_id,
      "venue_image_link": venue.image_link,
      "venue_name": venue.name
    }
    if(show.start_time > todayDate):
      upcoming_shows.append(temp_show)
    else: 
      past_shows.append(temp_show)
   
  artist.upcoming_shows = upcoming_shows
  artist.past_shows = past_shows  
  return render_template('pages/show_artist.html', artist=artist, shows=shows)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  form = ArtistForm(obj=artist)

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error = False
  form = ArtistForm(request.form)
  artist = Artist.query.get(artist_id)

  try: 
    artist.name = form.name.data
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    artist.genres = form.genres.data
    artist.website = form.website.data
    artist.facebook_link = form.facebook_link.data
    artist.seeking_venues = form.seeking_venues.data
    artist.seeking_description = form.seeking_description.data
    artist.image_link = form.image_link.data
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully updated!')
  except:
    db.session.rollback()
    flash('Artist ' + request.form['name'] + ' was unsuccessfully updated.')
    error = True
  finally:
    db.session.close()
  if error: 
    abort(500)
  else:
    return redirect(url_for('show_artist', artist_id=artist_id))
 

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  form = VenueForm(obj=venue)

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  error = False
  form = VenueForm(request.form)
  venue = Venue.query.get(venue_id)

  try: 
      #define changes in venue
      venue.name=form.name.data
      venue.city=form.city.data
      venue.address=form.address.data
      venue.state=form.state.data
      venue.phone=form.phone.data
      venue.image_link=form.image_link.data
      venue.facebook_link=form.facebook_link.data
      venue.genres=form.genres.data
      venue.website=form.website.data
      venue.seeking_talent=form.seeking_talent.data
      venue.seeking_description=form.seeking_description.data
      db.session.commit()
      flash('Venue ' + request.form['name'] + ' was successfully updated!')
  except: 
    db.session.rollback()
    flash('Error! Venue ' + request.form['name'] + ' was unsuccessfully updated.')
    error = True
  finally: 
    db.session.close()
  if error:
    abort(500)
  else: 
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():  
  error = False
  form = ArtistForm(request.form)
  try:
    #create new artist with form information
    artist = Artist(
      name=form.name.data,
      city=form.city.data,
      state=form.state.data,
      phone=form.phone.data,
      image_link=form.image_link.data,
      facebook_link=form.facebook_link.data,
      genres=form.genres.data,
      website=form.website.data,
      seeking_venues=form.seeking_venues.data,
      seeking_description=form.seeking_description.data,
    )
    db.session.add(artist)
    db.session.commit()
    artist_id = artist.id
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info)
  finally:
    db.session.close()
  if error: 
    flash('An error occured. Artist ' + request.form['name'] + ' failed to list.')
    return render_template('pages/home.html')
  else:
    return redirect(url_for('show_artist', artist_id=artist.id))


#  ----------------------------------------------------------------
#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():

  #get all shows
  shows = Show.query.all()
  showsData = []

  for show in shows: 
    temp = {}
    artist = Artist.query.get(show.artist_id)
    venue = Venue.query.get(show.venue_id)
    date = format_time(show.start_time)
    # date = str(show.start_time.strftime('%A')) + ', ' + str(show.start_time.strftime('%d')) + ' ' + str(show.start_time.strftime('%B')) + ' ' + str(show.start_time.year) + ' ' + str(show.start_time.strftime('%I')) + ':' + str(show.start_time.strftime('%M')) + ' ' + str(show.start_time.strftime('%p'))
    print(date)
    # print(show.start_time.strftime('%A'), show.start_time.day, show.start_time.month, show.start_time.year)
    # formattedDate = show.start_time.day
    #define a temporary obj with appropriate artist and venue fields to add to showsData
    temp = {
      "venue_id": show.venue_id,
      "venue_name": venue.name,
      "artist_id": show.artist_id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": date
    }
    showsData.append(temp)
    
  return render_template('pages/shows.html', shows=showsData)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  form = ShowForm(request.form)
  
  try:
    #create new show based on form data
    show = Show(
      artist_id=form.artist_id.data,
      venue_id=form.venue_id.data,
      start_time=form.start_time.data,
    )
    db.session.add(show)
    db.session.commit()
    show_id = show.id
    flash('Show was successfully listed!')
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info)
  finally:
    db.session.close()
  if error: 
    flash('An error occured. Show failed to list.')
    return render_template('pages/home.html')
  else:
    return redirect(url_for('shows'))


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
