import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { getClientLocations, createClientLocation, updateClientLocation, deleteClientLocation } from '../../services/api';

// Fix icônes Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const ClientsMap = () => {
  const [locations, setLocations] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [editingLocation, setEditingLocation] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    latitude: '',
    longitude: ''
  });

  useEffect(() => {
    loadLocations();
  }, []);

  const loadLocations = async () => {
    try {
      const response = await getClientLocations();
      setLocations(response.data);
    } catch (error) {
      console.error('Erreur:', error);
    }
  };

  const getMapBounds = () => {
    if (locations.length === 0) {
      return { center: [31.7917, -7.0926], zoom: 6 }; // Maroc par défaut
    }

    if (locations.length === 1) {
      return { 
        center: [locations[0].latitude, locations[0].longitude], 
        zoom: 10 
      };
    }

    // Calculer les limites
    const lats = locations.map(loc => loc.latitude);
    const lngs = locations.map(loc => loc.longitude);
    
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLng = Math.min(...lngs);
    const maxLng = Math.max(...lngs);
    
    // Centre
    const centerLat = (minLat + maxLat) / 2;
    const centerLng = (minLng + maxLng) / 2;
    
    // Zoom basé sur la distance
    const latDiff = maxLat - minLat;
    const lngDiff = maxLng - minLng;
    const maxDiff = Math.max(latDiff, lngDiff);
    
    let zoom = 10;
    if (maxDiff > 10) zoom = 4;
    else if (maxDiff > 5) zoom = 5;
    else if (maxDiff > 2) zoom = 6;
    else if (maxDiff > 1) zoom = 7;
    else if (maxDiff > 0.5) zoom = 8;
    else if (maxDiff > 0.1) zoom = 9;
    
    return { center: [centerLat, centerLng], zoom };
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingLocation) {
        await updateClientLocation(editingLocation.id, formData);
      } else {
        await createClientLocation(formData);
      }
      setShowModal(false);
      setEditingLocation(null);
      setFormData({ name: '', description: '', latitude: '', longitude: '' });
      loadLocations();
    } catch (error) {
      console.error('Erreur:', error);
    }
  };

  const handleEdit = (location) => {
    setEditingLocation(location);
    setFormData({
      name: location.name,
      description: location.description,
      latitude: location.latitude,
      longitude: location.longitude
    });
    setShowModal(true);
  };

  const handleDelete = async (locationId) => {
    if (confirm('Supprimer cette localisation ?')) {
      await deleteClientLocation(locationId);
      loadLocations();
    }
  };

  const mapBounds = getMapBounds();

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="bg-white rounded-xl shadow">
          <div className="p-6 border-b flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold">Carte des Clients</h1>
              <p className="text-gray-600">{locations.length} localisations</p>
            </div>
            <button
              onClick={() => setShowModal(true)}
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              + Ajouter Localisation
            </button>
          </div>

          <div className="h-96">
            <MapContainer
              center={mapBounds.center}
              zoom={mapBounds.zoom}
              style={{ height: '100%', width: '100%' }}
              key={`${locations.length}-${mapBounds.center[0]}-${mapBounds.center[1]}`}
            >
              <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              {locations.map((location) => (
                <Marker key={location.id} position={[location.latitude, location.longitude]}>
                  <Popup>
                    <div>
                      <h3 className="font-semibold">{location.name}</h3>
                      <p className="text-sm text-gray-600">{location.description}</p>
                      <div className="flex gap-2 mt-2">
                        <button
                          onClick={() => handleEdit(location)}
                          className="bg-blue-500 text-white px-2 py-1 text-xs rounded"
                        >
                          Modifier
                        </button>
                        <button
                          onClick={() => handleDelete(location.id)}
                          className="bg-red-500 text-white px-2 py-1 text-xs rounded"
                        >
                          Supprimer
                        </button>
                      </div>
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[10000]">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <h2 className="text-xl font-semibold mb-4">
              {editingLocation ? 'Modifier' : 'Ajouter'} Localisation
            </h2>
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">Nom</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="w-full border rounded px-3 py-2"
                  required
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  className="w-full border rounded px-3 py-2"
                  rows="2"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">Latitude</label>
                <input
                  type="number"
                  step="0.000001"
                  value={formData.latitude}
                  onChange={(e) => setFormData({...formData, latitude: e.target.value})}
                  className="w-full border rounded px-3 py-2"
                  required
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">Longitude</label>
                <input
                  type="number"
                  step="0.000001"
                  value={formData.longitude}
                  onChange={(e) => setFormData({...formData, longitude: e.target.value})}
                  className="w-full border rounded px-3 py-2"
                  required
                />
              </div>
              <div className="flex gap-3 justify-end">
                <button
                  type="button"
                  onClick={() => {
                    setShowModal(false);
                    setEditingLocation(null);
                    setFormData({ name: '', description: '', latitude: '', longitude: '' });
                  }}
                  className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                  {editingLocation ? 'Modifier' : 'Ajouter'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClientsMap;
