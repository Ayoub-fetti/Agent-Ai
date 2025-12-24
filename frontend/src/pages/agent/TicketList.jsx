import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import api from "../../services/api";

const TicketList = () => {
  const [tickets, setTickets] = useState([]);

  useEffect(() => {
    api.get("/tickets/").then((res) => setTickets(res.data));
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl mb-4">Liste des Tickets</h1>
      <div className="space-y-4">
        {tickets.map((ticket) => (
          <Link
            key={ticket.id}
            to={`/tickets/${ticket.id}`}
            className="block p-4 border rounded hover:bg-gray-50"
          >
            <h3 className="font-bold">{ticket.title}</h3>
            <p className="text-gray-600">#{ticket.number}</p>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default TicketList;
