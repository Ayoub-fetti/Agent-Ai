import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import api from '../../services/api';

// Enregistrer les composants Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const AgentDashboard = () => {
  const { logout, user } = useAuth();
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    total: 0,
    open: 0,
    pending: 0,
    closed: 0,
    processed: 0
  });

  useEffect(() => {
    fetchTickets();
  }, []);

  const fetchTickets = async () => {
    try {
      setLoading(true);
      const response = await api.get('/tickets/');
      const ticketsData = response.data;
      setTickets(ticketsData);
      
      // Calculer les statistiques
      const total = ticketsData.length;
      const open = ticketsData.filter(t => t.state_id === 2).length;
      const pending = ticketsData.filter(t => t.state_id === 1 || t.state_id === 3 || t.state_id === 4).length;
      const closed = ticketsData.filter(t => t.state_id === 5).length;
      
      setStats({
        total,
        open,
        pending,
        closed,
        processed: 0 // À adapter selon votre logique métier
      });
    } catch (error) {
      console.error('Erreur lors du chargement des tickets:', error);
    } finally {
      setLoading(false);
    }
  };

  // Préparer les données pour le graphique de tendance (7 derniers jours)
  const getTicketsByDate = () => {
    const last7Days = [];
    const today = new Date();
    
    for (let i = 6; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      last7Days.push(date.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' }));
    }
    
    const ticketsByDate = last7Days.map(date => {
      return tickets.filter(ticket => {
        if (!ticket.created_at) return false;
        const ticketDate = new Date(ticket.created_at).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' });
        return ticketDate === date;
      }).length;
    });
    
    return { labels: last7Days, data: ticketsByDate };
  };

  // Données pour le graphique de tendance
  const trendData = getTicketsByDate();
  const lineChartData = {
    labels: trendData.labels,
    datasets: [
      {
        label: 'Tickets créés',
        data: trendData.data,
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        fill: true,
        pointRadius: 5,
        pointHoverRadius: 7,
        pointBackgroundColor: 'rgb(59, 130, 246)',
        pointBorderColor: '#fff',
        pointBorderWidth: 2
      }
    ]
  };

  // Données pour le graphique en barres (tickets par statut)
  const barChartData = {
    labels: ['Ouvert', 'En attente', 'Rappel', 'Clos'],
    datasets: [
      {
        label: 'Nombre de tickets',
        data: [
          tickets.filter(t => t.state_id === 2).length,
          tickets.filter(t => t.state_id === 1 || t.state_id === 4).length,
          tickets.filter(t => t.state_id === 3).length,
          tickets.filter(t => t.state_id === 5).length
        ],
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(251, 191, 36, 0.8)',
          'rgba(249, 115, 22, 0.8)',
          'rgba(107, 114, 128, 0.8)'
        ],
        borderColor: [
          'rgb(59, 130, 246)',
          'rgb(251, 191, 36)',
          'rgb(249, 115, 22)',
          'rgb(107, 114, 128)'
        ],
        borderWidth: 2,
        borderRadius: 8
      }
    ]
  };

  // Données pour le graphique en donut (répartition des statuts)
  const doughnutChartData = {
    labels: ['Ouvert', 'En attente', 'Rappel', 'Clos'],
    datasets: [
      {
        data: [
          tickets.filter(t => t.state_id === 2).length,
          tickets.filter(t => t.state_id === 1 || t.state_id === 4).length,
          tickets.filter(t => t.state_id === 3).length,
          tickets.filter(t => t.state_id === 5).length
        ],
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(251, 191, 36, 0.8)',
          'rgba(249, 115, 22, 0.8)',
          'rgba(107, 114, 128, 0.8)'
        ],
        borderColor: [
          'rgb(59, 130, 246)',
          'rgb(251, 191, 36)',
          'rgb(249, 115, 22)',
          'rgb(107, 114, 128)'
        ],
        borderWidth: 3,
        hoverOffset: 8
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          font: {
            size: 12,
            family: "'Inter', sans-serif"
          },
          padding: 15,
          usePointStyle: true
        }
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: 12,
        titleFont: {
          size: 14,
          weight: 'bold'
        },
        bodyFont: {
          size: 12
        },
        cornerRadius: 8,
        displayColors: true
      }
    }
  };

  const lineChartOptions = {
    ...chartOptions,
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          stepSize: 1
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.05)'
        }
      },
      x: {
        grid: {
          display: false
        }
      }
    }
  };

  const barChartOptions = {
    ...chartOptions,
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          stepSize: 1
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.05)'
        }
      },
      x: {
        grid: {
          display: false
        }
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
        <div className="text-center">
          <i className="fas fa-spinner fa-spin text-4xl text-blue-600 mb-4"></i>
          <p className="text-gray-600 text-lg">Chargement du dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <i className="fas fa-chart-line text-3xl text-blue-600"></i>
              <h1 className="text-4xl font-bold text-gray-900">Dashboard Agent Technique</h1>
            </div>
            <p className="text-gray-600">
              Bienvenue, {user?.username || 'Agent'} • Vue d'ensemble de vos tickets
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to="/tickets"
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors duration-200 flex items-center gap-2 shadow-md hover:shadow-lg"
            >
              <i className="fas fa-ticket-alt"></i>
              Voir les Tickets
            </Link>
          </div>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Total Tickets */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow duration-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">Total Tickets</p>
                <p className="text-3xl font-bold text-gray-900">{stats.total}</p>
              </div>
              <div className="bg-blue-100 p-4 rounded-full">
                <i className="fas fa-ticket-alt text-2xl text-blue-600"></i>
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm">
              <span className="text-gray-500">Tous les tickets</span>
            </div>
          </div>

          {/* Tickets Ouverts */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow duration-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">Tickets Ouverts</p>
                <p className="text-3xl font-bold text-blue-600">{stats.open}</p>
              </div>
              <div className="bg-blue-100 p-4 rounded-full">
                <i className="fas fa-folder-open text-2xl text-blue-600"></i>
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm">
              <span className="text-gray-500">En cours de traitement</span>
            </div>
          </div>

          {/* Tickets En Attente */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow duration-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">En Attente</p>
                <p className="text-3xl font-bold text-yellow-600">{stats.pending}</p>
              </div>
              <div className="bg-yellow-100 p-4 rounded-full">
                <i className="fas fa-clock text-2xl text-yellow-600"></i>
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm">
              <span className="text-gray-500">En attente de traitement</span>
            </div>
          </div>

          {/* Tickets Clos */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow duration-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">Tickets Clos</p>
                <p className="text-3xl font-bold text-gray-600">{stats.closed}</p>
              </div>
              <div className="bg-gray-100 p-4 rounded-full">
                <i className="fas fa-check-circle text-2xl text-gray-600"></i>
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm">
              <span className="text-gray-500">Résolus et fermés</span>
            </div>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Line Chart - Tendance */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                <i className="fas fa-chart-line text-blue-600"></i>
                Tendance des Tickets (7 jours)
              </h2>
            </div>
            <div className="h-64">
              <Line data={lineChartData} options={lineChartOptions} />
            </div>
          </div>

          {/* Doughnut Chart - Répartition */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                <i className="fas fa-chart-pie text-blue-600"></i>
                Répartition par Statut
              </h2>
            </div>
            <div className="h-64">
              <Doughnut data={doughnutChartData} options={chartOptions} />
            </div>
          </div>
        </div>

        {/* Bar Chart - Tickets par Statut */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <i className="fas fa-chart-bar text-blue-600"></i>
              Distribution des Tickets par Statut
            </h2>
          </div>
          <div className="h-80">
            <Bar data={barChartData} options={barChartOptions} />
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <i className="fas fa-bolt text-yellow-500"></i>
            Actions Rapides
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link
              to="/tickets"
              className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all duration-200 flex items-center gap-3 group"
            >
              <div className="bg-blue-100 p-3 rounded-lg group-hover:bg-blue-200 transition-colors">
                <i className="fas fa-list text-blue-600 text-xl"></i>
              </div>
              <div>
                <p className="font-semibold text-gray-900">Voir tous les tickets</p>
                <p className="text-sm text-gray-500">Consulter la liste complète</p>
              </div>
            </Link>
            
            <button
              onClick={fetchTickets}
              className="p-4 border-2 border-gray-200 rounded-lg hover:border-green-500 hover:bg-green-50 transition-all duration-200 flex items-center gap-3 group"
            >
              <div className="bg-green-100 p-3 rounded-lg group-hover:bg-green-200 transition-colors">
                <i className="fas fa-sync-alt text-green-600 text-xl"></i>
              </div>
              <div>
                <p className="font-semibold text-gray-900">Actualiser</p>
                <p className="text-sm text-gray-500">Mettre à jour les données</p>
              </div>
            </button>

            <Link
              to="/tickets"
              className="p-4 border-2 border-gray-200 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-all duration-200 flex items-center gap-3 group"
            >
              <div className="bg-purple-100 p-3 rounded-lg group-hover:bg-purple-200 transition-colors">
                <i className="fas fa-filter text-purple-600 text-xl"></i>
              </div>
              <div>
                <p className="font-semibold text-gray-900">Filtrer les tickets</p>
                <p className="text-sm text-gray-500">Rechercher et filtrer</p>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentDashboard;