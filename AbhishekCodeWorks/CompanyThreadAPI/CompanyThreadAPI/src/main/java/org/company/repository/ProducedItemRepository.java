package org.company.repository;

import org.company.entity.ProducedItem;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ProducedItemRepository extends JpaRepository<ProducedItem, Long> {
    
    ProducedItem findTopByOrderByIdDesc();

}
