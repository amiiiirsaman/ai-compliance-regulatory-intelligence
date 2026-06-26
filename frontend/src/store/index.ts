import { configureStore } from '@reduxjs/toolkit'
import authReducer from './slices/authSlice'
import reviewsReducer from './slices/reviewsSlice'
import documentsReducer from './slices/documentsSlice'

export const store = configureStore({
  reducer: {
    auth: authReducer,
    reviews: reviewsReducer,
    documents: documentsReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }),
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
