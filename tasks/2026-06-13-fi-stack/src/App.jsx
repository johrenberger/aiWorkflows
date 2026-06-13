import React, { useState } from 'react';
import { PetVisitList } from './components/PetVisitList.jsx';
import { NewVisitForm } from './components/NewVisitForm.jsx';
import { PetTypeFilter } from './components/PetTypeFilter.jsx';

export function App() {
    const [selectedPetId, setSelectedPetId] = useState(8);
    const [refreshKey, setRefreshKey] = useState(0);

    const onVisitCreated = () => setRefreshKey((k) => k + 1);

    return (
        <main>
            <h1>PetClinic</h1>
            <section aria-labelledby="filter-heading">
                <h2 id="filter-heading">Find pets</h2>
                <PetTypeFilter />
            </section>
            <hr />
            <section aria-labelledby="visits-heading">
                <h2 id="visits-heading">
                    Visits for pet {selectedPetId}
                </h2>
                <p>
                    <label htmlFor="pet-id-input">Pet ID: </label>
                    <input
                        id="pet-id-input"
                        type="number"
                        min="1"
                        value={selectedPetId}
                        onChange={(e) =>
                            setSelectedPetId(parseInt(e.target.value, 10) || 1)
                        }
                        style={{ width: '5rem' }}
                    />
                </p>
                <PetVisitList
                    key={refreshKey}
                    petId={selectedPetId}
                />
            </section>
            <hr />
            <section aria-labelledby="new-visit-heading">
                <h2 id="new-visit-heading">Add a new visit</h2>
                <NewVisitForm
                    petId={selectedPetId}
                    onVisitCreated={onVisitCreated}
                />
            </section>
        </main>
    );
}
