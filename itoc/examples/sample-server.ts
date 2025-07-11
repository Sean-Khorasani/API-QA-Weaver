import express from 'express';
import bodyParser from 'body-parser';

const app = express();
app.use(bodyParser.json());

// In-memory user storage
let users: any[] = [
  { id: '1', name: 'John Doe', email: 'john@example.com', age: 30, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() },
  { id: '2', name: 'Jane Smith', email: 'jane@example.com', age: 25, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() }
];
let nextId = 3;

// Middleware to simulate variable response times
app.use((req, res, next) => {
  const delay = Math.random() * 100; // 0-100ms delay
  setTimeout(next, delay);
});

// GET /api/users
app.get('/api/users', (req, res) => {
  const limit = parseInt(req.query.limit as string) || 10;
  const offset = parseInt(req.query.offset as string) || 0;
  
  // Simulate occasional errors
  if (Math.random() < 0.05) {
    return res.status(500).json({ error: 'Internal server error' });
  }

  const paginatedUsers = users.slice(offset, offset + limit);
  
  res.json({
    users: paginatedUsers,
    total: users.length,
    limit,
    offset
  });
});

// POST /api/users
app.post('/api/users', (req, res) => {
  const { name, email, age } = req.body;
  
  // Validation
  if (!name || !email) {
    return res.status(400).json({ error: 'Name and email are required' });
  }

  if (name.length > 100) {
    return res.status(400).json({ error: 'Name is too long' });
  }

  // Check for duplicate email
  if (users.some(u => u.email === email)) {
    return res.status(400).json({ error: 'Email already exists' });
  }

  const newUser = {
    id: String(nextId++),
    name,
    email,
    age: age || null,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  };

  users.push(newUser);
  res.status(201).json(newUser);
});

// GET /api/users/:id
app.get('/api/users/:id', (req, res) => {
  const user = users.find(u => u.id === req.params.id);
  
  if (!user) {
    return res.status(404).json({ error: 'User not found' });
  }

  // Simulate occasional slow responses
  if (Math.random() < 0.1) {
    setTimeout(() => res.json(user), 500);
  } else {
    res.json(user);
  }
});

// PUT /api/users/:id
app.put('/api/users/:id', (req, res) => {
  const userIndex = users.findIndex(u => u.id === req.params.id);
  
  if (userIndex === -1) {
    return res.status(404).json({ error: 'User not found' });
  }

  const { name, email, age } = req.body;
  
  if (!name || !email) {
    return res.status(400).json({ error: 'Name and email are required' });
  }

  users[userIndex] = {
    ...users[userIndex],
    name,
    email,
    age: age || users[userIndex].age,
    updatedAt: new Date().toISOString()
  };

  res.json(users[userIndex]);
});

// DELETE /api/users/:id
app.delete('/api/users/:id', (req, res) => {
  const userIndex = users.findIndex(u => u.id === req.params.id);
  
  if (userIndex === -1) {
    return res.status(404).json({ error: 'User not found' });
  }

  users.splice(userIndex, 1);
  res.status(204).send();
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Sample server running on http://localhost:${PORT}`);
  console.log('API endpoints:');
  console.log('  GET    /api/users');
  console.log('  POST   /api/users');
  console.log('  GET    /api/users/:id');
  console.log('  PUT    /api/users/:id');
  console.log('  DELETE /api/users/:id');
});