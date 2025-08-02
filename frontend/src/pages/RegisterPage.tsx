/**
 * Register Page Component - currently not used as registration is handled in LoginPage
 * This file exists for future expansion if separate registration page is needed
 */

import React from 'react';
import { Navigate } from 'react-router-dom';

export default function RegisterPage(): JSX.Element {
  // Redirect to login page where registration is handled
  return <Navigate to="/login" replace />;
}