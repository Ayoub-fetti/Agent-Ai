import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../services/api';
import { toast } from 'react-toastify';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const CommercialDashboard = () => {
  const { logout, user } = useAuth();
  const [leads, setLeads] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [filters, setFilters] = useState({
    temperature: '',
    country: '',
    project_type: '',
    sector: '',
    min_score: '',
    is_contacted: '',
  });
  const [selectedLead, setSelectedLead] = useState(null);
  const [showSearchModal, setShowSearchModal] = useState(false);
  const [searchCountries, setSearchCountries] = useState(['Maroc', 'France', 'Canada']);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [leadToDelete, setLeadToDelete] = useState(null);

  useEffect(() => {
    fetchLeads();
    fetchStats();
  }, [filters]);

  const fetchLeads = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });
      params.append('ordering', '-score');
      params.append('page_size', '50');

      const response = await api.get(`/leads/?${params.toString()}`);
      setLeads(response.data.results || []);
    } catch (error) {
      console.error('Erreur lors du chargement des leads:', error);
      toast.error('Erreur lors du chargement des leads');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await api.get('/leads/stats/');
      setStats(response.data);
    } catch (error) {
      console.error('Erreur lors du chargement des stats:', error);
    }
  };

  const handleSearchLeads = async () => {
    if (searchCountries.length === 0) {
      toast.warning('Veuillez sélectionner au moins un pays');
      return;
    }

    try {
      setSearching(true);
      setShowSearchModal(false);
      
      toast.info('Génération des leads en cours...', { autoClose: 2000 });
      
      const response = await api.post('/leads/generate-with-ai/', {
        countries: searchCountries,
      });
      
      if (response.data.success) {
        toast.success(
          `${response.data.message}\nLeads générés: ${response.data.total_generated}\nLeads créés: ${response.data.total_created}`,
          { autoClose: 5000 }
        );
        
        fetchLeads();
        fetchStats();
      } else {
        toast.error(`Erreur: ${response.data.error}`);
      }
    } catch (error) {
      console.error('Erreur lors de la génération:', error);
      toast.error('Erreur lors de la génération de leads');
    } finally {
      setSearching(false);
    }
  };

  const handleUpdateLead = async (leadId, updates) => {
    try {
      await api.patch(`/leads/${leadId}/update/`, updates);
      toast.success('Lead mis à jour avec succès');
      fetchLeads();
      fetchStats();
      if (selectedLead?.id === leadId) {
        setSelectedLead({ ...selectedLead, ...updates });
      }
    } catch (error) {
      console.error('Erreur lors de la mise à jour:', error);
      toast.error('Erreur lors de la mise à jour du lead');
    }
  };

  const handleReanalyze = async (leadId) => {
    try {
      const response = await api.post(`/leads/${leadId}/reanalyze/`);
      if (response.data.success) {
        toast.success('Lead réanalysé avec succès');
        fetchLeads();
        fetchStats();
        if (selectedLead?.id === leadId) {
          const updatedLead = leads.find(l => l.id === leadId);
          setSelectedLead(updatedLead);
        }
      }
    } catch (error) {
      console.error('Erreur lors de la réanalyse:', error);
      toast.error('Erreur lors de la réanalyse');
    }
  };

  const handleDeleteLead = async () => {
    if (!leadToDelete) return;

    try {
      await api.delete(`/leads/${leadToDelete}/delete/`);
      toast.success('Lead supprimé avec succès');
      setShowDeleteModal(false);
      setLeadToDelete(null);
      setSelectedLead(null);
      fetchLeads();
      fetchStats();
    } catch (error) {
      console.error('Erreur lors de la suppression:', error);
      toast.error('Erreur lors de la suppression du lead');
    }
  };

  const getTemperatureColor = (temperature) => {
    switch (temperature) {
      case 'chaud':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'tiede':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'froid':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 70) return 'text-red-600 font-bold';
    if (score >= 40) return 'text-yellow-600 font-semibold';
    return 'text-blue-600';
  };

  const temperatureChartData = stats ? {
    labels: ['Chaud', 'Tiède', 'Froid'],
    datasets: [{
      data: [
        stats.by_temperature?.chaud || 0,
        stats.by_temperature?.tiede || 0,
        stats.by_temperature?.froid || 0,
      ],
      backgroundColor: ['#ef4444', '#eab308', '#3b82f6'],
    }],
  } : null;

  const countryChartData = stats && stats.by_country ? {
    labels: Object.keys(stats.by_country),
    datasets: [{
      label: 'Leads par pays',
      data: Object.values(stats.by_country),
      backgroundColor: '#3b82f6',
    }],
  } : null;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Dashboard Agent Commercial</h1>
              <p className="text-sm text-gray-500">Gestion des leads GTB/GTEB</p>
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={() => setShowSearchModal(true)}
                disabled={searching}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
              >
                <i className="fas fa-magic"></i>
                {searching ? 'Génération...' : 'Générer avec l\'IA'}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Statistiques */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Total Leads</p>
                  <p className="text-3xl font-bold text-gray-900">{stats.total}</p>
                </div>
                <div className="bg-blue-100 p-3 rounded-lg">
                  <i className="fas fa-users text-blue-600 text-2xl"></i>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Leads Chauds</p>
                  <p className="text-3xl font-bold text-red-600">{stats.by_temperature?.chaud || 0}</p>
                </div>
                <div className="bg-red-100 p-3 rounded-lg">
                  <i className="fas fa-fire text-red-600 text-2xl"></i>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Contactés</p>
                  <p className="text-3xl font-bold text-green-600">{stats.contacted}</p>
                </div>
                <div className="bg-green-100 p-3 rounded-lg">
                  <i className="fas fa-phone text-green-600 text-2xl"></i>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Score Moyen</p>
                  <p className="text-3xl font-bold text-purple-600">{stats.avg_score || 0}</p>
                </div>
                <div className="bg-purple-100 p-3 rounded-lg">
                  <i className="fas fa-star text-purple-600 text-2xl"></i>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Graphiques */}
        {stats && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Répartition par Température</h2>
              {temperatureChartData && (
                <div className="h-64">
                  <Doughnut data={temperatureChartData} />
                </div>
              )}
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Leads par Pays</h2>
              {countryChartData && (
                <div className="h-64">
                  <Bar data={countryChartData} />
                </div>
              )}
            </div>
          </div>
        )}

        {/* Filtres */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Filtres</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <select
              value={filters.temperature}
              onChange={(e) => setFilters({ ...filters, temperature: e.target.value })}
              className="border border-gray-300 rounded-lg px-3 py-2"
            >
              <option value="">Toutes températures</option>
              <option value="chaud">Chaud</option>
              <option value="tiede">Tiède</option>
              <option value="froid">Froid</option>
            </select>

            <select
              value={filters.country}
              onChange={(e) => setFilters({ ...filters, country: e.target.value })}
              className="border border-gray-300 rounded-lg px-3 py-2"
            >
              <option value="">Tous pays</option>
              <option value="Maroc">Maroc</option>
              <option value="France">France</option>
              <option value="Canada">Canada</option>
            </select>

            <select
              value={filters.project_type}
              onChange={(e) => setFilters({ ...filters, project_type: e.target.value })}
              className="border border-gray-300 rounded-lg px-3 py-2"
            >
              <option value="">Tous types</option>
              <option value="GTB">GTB</option>
              <option value="GTEB">GTEB</option>
              <option value="CVC">CVC</option>
              <option value="supervision">Supervision</option>
              <option value="electricite">Électricité</option>
            </select>

            <input
              type="number"
              placeholder="Score min"
              value={filters.min_score}
              onChange={(e) => setFilters({ ...filters, min_score: e.target.value })}
              className="border border-gray-300 rounded-lg px-3 py-2"
            />

            <select
              value={filters.is_contacted}
              onChange={(e) => setFilters({ ...filters, is_contacted: e.target.value })}
              className="border border-gray-300 rounded-lg px-3 py-2"
            >
              <option value="">Tous</option>
              <option value="true">Contactés</option>
              <option value="false">Non contactés</option>
            </select>

            <button
              onClick={() => setFilters({
                temperature: '',
                country: '',
                project_type: '',
                sector: '',
                min_score: '',
                is_contacted: '',
              })}
              className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300"
            >
              Réinitialiser
            </button>
          </div>
        </div>

        {/* Liste des leads */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-900">Liste des Leads ({leads.length})</h2>
          </div>

          {loading ? (
            <div className="p-8 text-center">
              <i className="fas fa-spinner fa-spin text-3xl text-gray-400"></i>
              <p className="mt-4 text-gray-500">Chargement...</p>
            </div>
          ) : leads.length === 0 ? (
            <div className="p-8 text-center">
              <i className="fas fa-inbox text-4xl text-gray-400 mb-4"></i>
              <p className="text-gray-500">Aucun lead trouvé</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {leads.map((lead) => (
                <div
                  key={lead.id}
                  className="p-6 hover:bg-gray-50 cursor-pointer"
                  onClick={() => setSelectedLead(lead)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900">{lead.organization_name}</h3>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getTemperatureColor(lead.temperature)}`}>
                          {lead.temperature?.toUpperCase()}
                        </span>
                        <span className={`text-lg font-bold ${getScoreColor(lead.score)}`}>
                          {lead.score}/100
                        </span>
                      </div>
                      <p className="text-gray-700 mb-2">{lead.title}</p>
                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        <span><i className="fas fa-map-marker-alt mr-1"></i>{lead.city}, {lead.country}</span>
                        {lead.project_type && (
                          <span><i className="fas fa-tag mr-1"></i>{lead.project_type}</span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      {lead.is_contacted && (
                        <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">
                          Contacté
                        </span>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedLead(lead);
                        }}
                        className="text-blue-600 hover:text-blue-700"
                      >
                        <i className="fas fa-eye"></i>
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setLeadToDelete(lead.id);
                          setShowDeleteModal(true);
                        }}
                        className="text-red-600 hover:text-red-700"
                      >
                        <i className="fas fa-trash"></i>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Modal de génération IA */}
      {showSearchModal && (
        <div className="fixed inset-0 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Générer des Leads avec l'IA</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Pays à cibler
                </label>
                <div className="space-y-2">
                  {['Maroc', 'France', 'Canada'].map((country) => (
                    <label key={country} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={searchCountries.includes(country)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSearchCountries([...searchCountries, country]);
                          } else {
                            setSearchCountries(searchCountries.filter(c => c !== country));
                          }
                        }}
                        className="mr-2"
                      />
                      {country}
                    </label>
                  ))}
                </div>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={handleSearchLeads}
                  disabled={searching || searchCountries.length === 0}
                  className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {searching ? 'Génération en cours...' : 'Générer avec l\'IA'}
                </button>
                <button
                  onClick={() => setShowSearchModal(false)}
                  className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300"
                >
                  Annuler
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal de confirmation de suppression */}
      {showDeleteModal && (
        <div className="fixed inset-0 backdrop-blur-sm  flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <div className="flex items-center gap-3 mb-4">
              <div className="bg-red-100 p-3 rounded-full">
                <i className="fas fa-exclamation-triangle text-red-600 text-xl"></i>
              </div>
              <h2 className="text-xl font-bold text-gray-900">Confirmer la suppression</h2>
            </div>
            <p className="text-gray-600 mb-6">
              Êtes-vous sûr de vouloir supprimer ce lead ? Cette action est irréversible.
            </p>
            <div className="flex gap-3">
              <button
                onClick={handleDeleteLead}
                className="flex-1 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
              >
                Supprimer
              </button>
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setLeadToDelete(null);
                }}
                className="flex-1 bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300"
              >
                Annuler
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de détails du lead */}
      {selectedLead && (
        <div className="fixed inset-0 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold text-gray-900">Détails du Lead</h2>
              <button
                onClick={() => setSelectedLead(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <i className="fas fa-times text-2xl"></i>
              </button>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Organisation</label>
                  <p className="text-gray-900 font-semibold">{selectedLead.organization_name}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Score / Température</label>
                  <div className="flex items-center gap-2">
                    <span className={`text-xl font-bold ${getScoreColor(selectedLead.score)}`}>
                      {selectedLead.score}/100
                    </span>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getTemperatureColor(selectedLead.temperature)}`}>
                      {selectedLead.temperature?.toUpperCase()}
                    </span>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Titre</label>
                <p className="text-gray-900">{selectedLead.title}</p>
              </div>

              {selectedLead.description && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Description</label>
                  <p className="text-gray-900">{selectedLead.description}</p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Localisation</label>
                  <p className="text-gray-900">{selectedLead.city}, {selectedLead.country}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Type de projet</label>
                  <p className="text-gray-900">{selectedLead.project_type || 'Non spécifié'}</p>
                </div>
              </div>

              {selectedLead.score_justification && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Justification du score</label>
                  <p className="text-gray-900 bg-gray-50 p-3 rounded-lg">{selectedLead.score_justification}</p>
                </div>
              )}

              <div className="flex gap-3 pt-4 border-t border-gray-200">
                <button
                  onClick={() => handleUpdateLead(selectedLead.id, { is_contacted: !selectedLead.is_contacted })}
                  className={`flex-1 px-4 py-2 rounded-lg ${
                    selectedLead.is_contacted
                      ? 'bg-green-600 text-white hover:bg-green-700'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  {selectedLead.is_contacted ? 'Marquer comme non contacté' : 'Marquer comme contacté'}
                </button>
                <button
                  onClick={() => handleReanalyze(selectedLead.id)}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                >
                  Réanalyser
                </button>
                <button
                  onClick={() => {
                    setLeadToDelete(selectedLead.id);
                    setShowDeleteModal(true);
                  }}
                  className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
                >
                  Supprimer
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CommercialDashboard;
