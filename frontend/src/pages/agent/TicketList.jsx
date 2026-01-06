import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import api from "../../services/api";

const TicketList = () => {
  const [tickets, setTickets] = useState([]);
  const [filteredTickets, setFilteredTickets] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const ticketsPerPage = 10;

  const getstatusBadgeColor = (stateId) => {
    switch (stateId) {
      case 1:
        return "bg-green-100 text-green-800 border-green-200";
      case 2:
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case 3:
        return "bg-orange-100 text-orange-800 border-orange-200";
      case 4:
        return "bg-gray-100 text-gray-800 border-gray-200";
      case 5:
        return "bg-gray-100 text-gray-800 border-gray-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getstatusLabel = (stateId) => {
    switch (stateId) {
      case 1:
        return "Nouveau";           // Au lieu de "En attente de cloture"
      case 2:
        return "Ouvert";
      case 3:
        return "Rappel en attente";
      case 4:
        return "En attente de clôture";
      case 5:
        return "Fermé";
      default:
        return stateId ? `Statut ${stateId}` : "Inconnu";
    }
  };

  useEffect(() => {
    setLoading(true);
    api
      .get("/tickets/")
      .then((res) => {
        setTickets(res.data);
        setFilteredTickets(res.data);
      })
      .catch((err) => {
        console.error("Error fetching tickets:", err);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    if (searchQuery.trim() === "") {
      setFilteredTickets(tickets);
      setCurrentPage(1);
    } else {
      const filtered = tickets.filter(
        (ticket) =>
          ticket.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          ticket.number?.toString().includes(searchQuery) ||
          ticket.id?.toString().includes(searchQuery) ||
          getstatusLabel(ticket.state_id)?.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setFilteredTickets(filtered);
      setCurrentPage(1);
    }
  }, [searchQuery, tickets]);

  const totalPages = Math.ceil(filteredTickets.length / ticketsPerPage);
  const startIndex = (currentPage - 1) * ticketsPerPage;
  const endIndex = startIndex + ticketsPerPage;
  const currentTickets = filteredTickets.slice(startIndex, endIndex);

  const handlePageChange = (page) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
        <div className="text-center">
          <i className="fas fa-spinner fa-spin text-4xl text-blue-600 mb-4"></i>
          <p className="text-gray-600 text-lg">Chargement des tickets...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <i className="fas fa-ticket-alt text-3xl text-blue-600"></i>
            <h1 className="text-4xl font-bold text-gray-900">Liste des Tickets</h1>
          </div>
          <p className="text-gray-600 mt-2">
            {filteredTickets.length} ticket{filteredTickets.length > 1 ? "s" : ""} trouvé{filteredTickets.length > 1 ? "s" : ""}
          </p>
        </div>

        {/* Search Bar */}
        <div className="mb-6">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <i className="fas fa-search text-gray-400"></i>
            </div>
            <input
              type="text"
              placeholder="Rechercher par titre, numéro, email ou status..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm transition-all duration-200"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-400 hover:text-gray-600 transition-colors"
              >
                <i className="fas fa-times"></i>
              </button>
            )}
          </div>
        </div>

        {/* Tickets List */}
        {currentTickets.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
            <i className="fas fa-inbox text-5xl text-gray-300 mb-4"></i>
            <p className="text-gray-600 text-lg">
              {searchQuery ? "Aucun ticket ne correspond à votre recherche" : "Aucun ticket disponible"}
            </p>
          </div>
        ) : (
          <div className="space-y-4 mb-8">
            {currentTickets.map((ticket) => (
              <Link
                key={ticket.id}
                to={`/tickets/${ticket.id}`}
                className="block bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md hover:border-blue-300 transition-all duration-200 transform hover:-translate-y-1"
              >
                <div className="p-6">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900 truncate">
                          {ticket.title || "Sans titre"}
                        </h3>
                        {ticket.state_id && (
                          <span
                            className={`px-3 py-1 rounded-full text-xs font-medium border ${getstatusBadgeColor(
                              ticket.state_id
                            )}`}
                          >
                            {getstatusLabel(ticket.state_id)}
                          </span>
                        )}
                      </div>
                      <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600 mt-3">
                        <div className="flex items-center gap-2">
                          <i className="fas fa-hashtag text-gray-400"></i>
                          <span className="font-mono">#{ticket.number || ticket.id}</span>
                        </div>
                        {ticket.customer_id && (
                          <div className="flex items-center gap-2">
                            <i className="fas fa-user text-gray-400"></i>
                            <span className="truncate max-w-xs">Client #{ticket.customer_id}</span>
                          </div>
                        )}
                        {ticket.created_at && (
                          <div className="flex items-center gap-2">
                            <i className="fas fa-calendar text-gray-400"></i>
                            <span>{new Date(ticket.created_at).toLocaleDateString("fr-FR")}</span>
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex-shrink-0">
                      <i className="fas fa-chevron-right text-gray-400 text-xl"></i>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 flex-wrap">
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className="px-4 py-2 rounded-lg border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              <i className="fas fa-chevron-left"></i>
              <span>Précédent</span>
            </button>

            <div className="flex items-center gap-1">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => {
                if (
                  page === 1 ||
                  page === totalPages ||
                  (page >= currentPage - 2 && page <= currentPage + 2)
                ) {
                  return (
                    <button
                      key={page}
                      onClick={() => handlePageChange(page)}
                      className={`px-4 py-2 rounded-lg border transition-colors ${
                        currentPage === page
                          ? "bg-blue-600 text-white border-blue-600"
                          : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                      }`}
                    >
                      {page}
                    </button>
                  );
                } else if (
                  page === currentPage - 3 ||
                  page === currentPage + 3
                ) {
                  return (
                    <span key={page} className="px-2 text-gray-500">
                      ...
                    </span>
                  );
                }
                return null;
              })}
            </div>

            <button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="px-4 py-2 rounded-lg border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              <span>Suivant</span>
              <i className="fas fa-chevron-right"></i>
            </button>
          </div>
        )}

        {/* Page Info */}
        {totalPages > 1 && (
          <div className="mt-4 text-center text-sm text-gray-600">
            Page {currentPage} sur {totalPages}
          </div>
        )}
      </div>
    </div>
  );
};

export default TicketList;
